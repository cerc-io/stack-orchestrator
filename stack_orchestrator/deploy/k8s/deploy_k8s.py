# Copyright © 2023 Vulcanize
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http:#www.gnu.org/licenses/>.

from datetime import datetime, timezone

from pathlib import Path
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from typing import Any, Dict, List, Optional, cast

from stack_orchestrator import constants
from stack_orchestrator.deploy.deployer import (
    Deployer,
    DeployerConfigGenerator,
    DeployerException,
)
from stack_orchestrator.deploy.k8s.helpers import (
    check_mounts_compatible,
    create_cluster,
    destroy_cluster,
    get_kind_cluster,
    is_image_available_locally,
    load_images_into_kind,
)
from stack_orchestrator.deploy.k8s.helpers import (
    install_ingress_for_kind,
    update_caddy_ingress_image,
    wait_for_ingress_in_kind,
    is_ingress_running,
)
from stack_orchestrator.deploy.k8s.helpers import (
    pods_in_deployment,
    containers_in_pod,
    log_stream_from_string,
)
from stack_orchestrator.deploy.k8s.helpers import (
    generate_kind_config,
    generate_high_memlock_spec_json,
)
from stack_orchestrator.deploy.k8s.cluster_info import ClusterInfo
from stack_orchestrator.opts import opts
from stack_orchestrator.deploy.deployment_context import DeploymentContext
from stack_orchestrator.util import error_exit


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def _check_delete_exception(e: ApiException) -> None:
    if e.status == 404:
        if opts.o.debug:
            print("Failed to delete object, continuing")
    else:
        error_exit(f"k8s api error: {e}")


def _create_runtime_class(name: str, handler: str):
    """Create a RuntimeClass resource for custom containerd runtime handlers.

    RuntimeClass allows pods to specify which runtime handler to use, enabling
    different pods to have different rlimit profiles (e.g., high-memlock).

    Args:
        name: The name of the RuntimeClass resource
        handler: The containerd runtime handler name
            (must match containerdConfigPatches)
    """
    api = client.NodeV1Api()
    runtime_class = client.V1RuntimeClass(
        api_version="node.k8s.io/v1",
        kind="RuntimeClass",
        metadata=client.V1ObjectMeta(name=name),
        handler=handler,
    )
    try:
        api.create_runtime_class(runtime_class)
        if opts.o.debug:
            print(f"Created RuntimeClass: {name}")
    except ApiException as e:
        if e.status == 409:  # Already exists
            if opts.o.debug:
                print(f"RuntimeClass {name} already exists")
        else:
            raise


class K8sDeployer(Deployer):
    name: str = "k8s"
    type: str
    core_api: client.CoreV1Api
    apps_api: client.AppsV1Api
    batch_api: client.BatchV1Api
    networking_api: client.NetworkingV1Api
    k8s_namespace: str
    kind_cluster_name: str
    skip_cluster_management: bool
    cluster_info: ClusterInfo
    deployment_dir: Path
    deployment_context: DeploymentContext

    def __init__(
        self,
        type,
        deployment_context: DeploymentContext,
        compose_files,
        compose_project_name,
        compose_env_file,
        job_compose_files=None,
    ) -> None:
        self.type = type
        self.skip_cluster_management = False
        self.image_overrides = None
        self.k8s_namespace = "default"  # Will be overridden below if context exists
        # TODO: workaround pending refactoring above to cope with being
        # created with a null deployment_context
        if deployment_context is None:
            return
        self.deployment_dir = deployment_context.deployment_dir
        self.deployment_context = deployment_context
        # kind cluster name comes from cluster-id — which kind cluster this
        # deployment attaches to. Shared across deployments that join the
        # same cluster. compose_project_name is kept as a parameter for
        # interface compatibility with the compose deployer path.
        cluster_id = deployment_context.get_cluster_id()
        deployment_id = deployment_context.get_deployment_id()
        self.kind_cluster_name = (
            deployment_context.spec.get_kind_cluster_name() or cluster_id
        )
        self.cluster_info = ClusterInfo()
        # stack.name may be an absolute path (from spec "stack:" key after
        # path resolution). Extract just the directory basename for labels.
        raw_name = deployment_context.stack.name if deployment_context else ""
        stack_name = Path(raw_name).name if raw_name else ""
        # Namespace: spec override wins; else derive from stack name; else
        # fall back to deployment-id. (On older deployment.yml files without
        # deployment-id, get_deployment_id() returns cluster-id — same as
        # the pre-decouple behavior.)
        self.k8s_namespace = deployment_context.spec.get_namespace() or (
            f"laconic-{stack_name}" if stack_name else f"laconic-{deployment_id}"
        )
        self.cluster_info = ClusterInfo()
        # app_name comes from deployment-id so each deployment owns its own
        # k8s resource names, even when multiple deployments share a cluster.
        self.cluster_info.int(
            compose_files,
            compose_env_file,
            deployment_id,
            deployment_context.spec,
            stack_name=stack_name,
        )
        # Initialize job compose files if provided
        if job_compose_files:
            self.cluster_info.init_jobs(job_compose_files)
        if opts.o.debug:
            print(f"Deployment dir: {deployment_context.deployment_dir}")
            print(f"Compose files: {compose_files}")
            print(f"Job compose files: {job_compose_files}")
            print(f"Project name: {compose_project_name}")
            print(f"Env file: {compose_env_file}")
            print(f"Type: {type}")

    def connect_api(self):
        if self.is_kind():
            config.load_kube_config(context=f"kind-{self.kind_cluster_name}")
        else:
            # Get the config file and pass to load_kube_config()
            config.load_kube_config(
                config_file=self.deployment_dir.joinpath(
                    constants.kube_config_filename
                ).as_posix()
            )
        self.core_api = client.CoreV1Api()
        self.networking_api = client.NetworkingV1Api()
        self.apps_api = client.AppsV1Api()
        self.batch_api = client.BatchV1Api()
        self.custom_obj_api = client.CustomObjectsApi()

    def _ensure_namespace(self):
        """Create the deployment namespace if it doesn't exist.

        Stamps the namespace with a `laconic.com/deployment-dir`
        annotation so that a subsequent `deployment start` from a
        different deployment dir — which would otherwise silently
        patch this deployment's k8s resources in place — fails with
        a clear error directing at the `namespace:` spec override.
        """
        if opts.o.dry_run:
            print(f"Dry run: would create namespace {self.k8s_namespace}")
            return
        owner_key = "laconic.com/deployment-dir"
        my_dir = str(Path(self.deployment_dir).resolve())
        try:
            existing = self.core_api.read_namespace(name=self.k8s_namespace)
        except ApiException as e:
            if e.status != 404:
                raise
            existing = None

        if existing is None:
            ns = client.V1Namespace(
                metadata=client.V1ObjectMeta(
                    name=self.k8s_namespace,
                    labels=self.cluster_info._stack_labels(),
                    annotations={owner_key: my_dir},
                )
            )
            self.core_api.create_namespace(body=ns)
            if opts.o.debug:
                print(f"Created namespace {self.k8s_namespace} " f"owned by {my_dir}")
            return

        annotations = (existing.metadata.annotations or {}) if existing.metadata else {}
        owner = annotations.get(owner_key)
        if owner and owner != my_dir:
            raise DeployerException(
                f"Namespace '{self.k8s_namespace}' is already owned by "
                f"another deployment at:\n  {owner}\n"
                f"\nThis deployment is at:\n  {my_dir}\n"
                "\nTwo deployments of the same stack sharing a cluster "
                "cannot share a namespace — every namespace-scoped "
                "resource (Deployment, ConfigMaps, Services, PVCs) "
                "would collide and silently patch each other.\n"
                "\nFix: add an explicit `namespace:` override to this "
                "deployment's spec.yml so it lands in its own "
                "namespace. For example:\n"
                f"  namespace: {self.k8s_namespace}-<suffix>\n"
                "\n(k8s namespace names must be lowercase alphanumeric "
                "plus '-', start and end with an alphanumeric character, "
                "≤63 chars.)"
            )
        if not owner:
            # Legacy namespace (pre-dates this check) or user-created.
            # Adopt it by stamping the ownership annotation so
            # subsequent conflicting deployments fail loudly.
            patch = {"metadata": {"annotations": {owner_key: my_dir}}}
            self.core_api.patch_namespace(name=self.k8s_namespace, body=patch)
            if opts.o.debug:
                print(
                    f"Adopted existing namespace {self.k8s_namespace} "
                    f"as owned by {my_dir}"
                )
        elif opts.o.debug:
            print(f"Namespace {self.k8s_namespace} already owned by {my_dir}")

    def _delete_namespace(self):
        """Delete the deployment namespace and all resources within it."""
        if opts.o.dry_run:
            print(f"Dry run: would delete namespace {self.k8s_namespace}")
            return
        try:
            self.core_api.delete_namespace(name=self.k8s_namespace)
            if opts.o.debug:
                print(f"Deleted namespace {self.k8s_namespace}")
        except ApiException as e:
            if e.status == 404:
                if opts.o.debug:
                    print(f"Namespace {self.k8s_namespace} not found")
            else:
                raise

    def _wait_for_namespace_gone(self, timeout_seconds: int = 120):
        """Wait for namespace to finish terminating."""
        if opts.o.dry_run:
            return
        import time

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                ns = self.core_api.read_namespace(name=self.k8s_namespace)
                if ns.status and ns.status.phase == "Terminating":
                    if opts.o.debug:
                        print(
                            f"Waiting for namespace {self.k8s_namespace}"
                            " to finish terminating..."
                        )
                    time.sleep(2)
                    continue
                # Namespace exists and is Active — shouldn't happen after delete
                break
            except ApiException as e:
                if e.status == 404:
                    # Gone — success
                    return
                raise
        # If we get here, namespace still exists after timeout
        try:
            self.core_api.read_namespace(name=self.k8s_namespace)
            print(
                f"Warning: namespace {self.k8s_namespace} still exists"
                f" after {timeout_seconds}s"
            )
        except ApiException as e:
            if e.status == 404:
                return
            raise

    def _delete_resources_by_label(self, label_selector: str, delete_volumes: bool):
        """Delete only this stack's resources from a shared namespace."""
        ns = self.k8s_namespace
        if opts.o.dry_run:
            print(f"Dry run: would delete resources with {label_selector} in {ns}")
            return

        # Deployments
        try:
            deps = self.apps_api.list_namespaced_deployment(
                namespace=ns, label_selector=label_selector
            )
            for dep in deps.items:
                print(f"Deleting Deployment {dep.metadata.name}")
                self.apps_api.delete_namespaced_deployment(
                    name=dep.metadata.name, namespace=ns
                )
        except ApiException as e:
            _check_delete_exception(e)

        # Jobs
        try:
            jobs = self.batch_api.list_namespaced_job(
                namespace=ns, label_selector=label_selector
            )
            for job in jobs.items:
                print(f"Deleting Job {job.metadata.name}")
                self.batch_api.delete_namespaced_job(
                    name=job.metadata.name,
                    namespace=ns,
                    body=client.V1DeleteOptions(propagation_policy="Background"),
                )
        except ApiException as e:
            _check_delete_exception(e)

        # Services (NodePorts created by SO)
        try:
            svcs = self.core_api.list_namespaced_service(
                namespace=ns, label_selector=label_selector
            )
            for svc in svcs.items:
                print(f"Deleting Service {svc.metadata.name}")
                self.core_api.delete_namespaced_service(
                    name=svc.metadata.name, namespace=ns
                )
        except ApiException as e:
            _check_delete_exception(e)

        # Ingresses
        try:
            ings = self.networking_api.list_namespaced_ingress(
                namespace=ns, label_selector=label_selector
            )
            for ing in ings.items:
                print(f"Deleting Ingress {ing.metadata.name}")
                self.networking_api.delete_namespaced_ingress(
                    name=ing.metadata.name, namespace=ns
                )
        except ApiException as e:
            _check_delete_exception(e)

        # ConfigMaps
        try:
            cms = self.core_api.list_namespaced_config_map(
                namespace=ns, label_selector=label_selector
            )
            for cm in cms.items:
                print(f"Deleting ConfigMap {cm.metadata.name}")
                self.core_api.delete_namespaced_config_map(
                    name=cm.metadata.name, namespace=ns
                )
        except ApiException as e:
            _check_delete_exception(e)

        # PVCs (only if --delete-volumes)
        if delete_volumes:
            try:
                pvcs = self.core_api.list_namespaced_persistent_volume_claim(
                    namespace=ns, label_selector=label_selector
                )
                for pvc in pvcs.items:
                    print(f"Deleting PVC {pvc.metadata.name}")
                    self.core_api.delete_namespaced_persistent_volume_claim(
                        name=pvc.metadata.name, namespace=ns
                    )
            except ApiException as e:
                _check_delete_exception(e)

    def _create_volume_data(self):  # noqa: C901
        # Create the host-path-mounted PVs for this deployment
        pvs = self.cluster_info.get_pvs()
        for pv in pvs:
            if opts.o.debug:
                print(f"Sending this pv: {pv}")
            if not opts.o.dry_run:
                try:
                    pv_resp = self.core_api.read_persistent_volume(
                        name=pv.metadata.name
                    )
                    if pv_resp:
                        # If PV is in Released state (stale claimRef from a
                        # previous deployment), clear the claimRef so a new
                        # PVC can bind to it. This happens after stop+start
                        # because stop deletes the namespace (and PVCs) but
                        # preserves PVs by default.
                        if pv_resp.status and pv_resp.status.phase == "Released":
                            print(
                                f"PV {pv.metadata.name} is Released, "
                                "clearing claimRef for rebinding"
                            )
                            pv_resp.spec.claim_ref = None
                            self.core_api.patch_persistent_volume(
                                name=pv.metadata.name,
                                body={"spec": {"claimRef": None}},
                            )
                        elif opts.o.debug:
                            print("PVs already present:")
                            print(f"{pv_resp}")
                        continue
                except ApiException as e:
                    if e.status != 404:
                        raise

                pv_resp = self.core_api.create_persistent_volume(body=pv)
                if opts.o.debug:
                    print("PVs created:")
                    print(f"{pv_resp}")

        # Figure out the PVCs for this deployment
        pvcs = self.cluster_info.get_pvcs()
        for pvc in pvcs:
            if opts.o.debug:
                print(f"Sending this pvc: {pvc}")

            if not opts.o.dry_run:
                try:
                    pvc_resp = self.core_api.read_namespaced_persistent_volume_claim(
                        name=pvc.metadata.name, namespace=self.k8s_namespace
                    )
                    if pvc_resp:
                        if opts.o.debug:
                            print("PVCs already present:")
                            print(f"{pvc_resp}")
                        continue
                except ApiException as e:
                    if e.status != 404:
                        raise

                pvc_resp = self.core_api.create_namespaced_persistent_volume_claim(
                    body=pvc, namespace=self.k8s_namespace
                )
                if opts.o.debug:
                    print("PVCs created:")
                    print(f"{pvc_resp}")

        # Figure out the ConfigMaps for this deployment
        config_maps = self.cluster_info.get_configmaps()
        for cfg_map in config_maps:
            if opts.o.debug:
                print(f"Sending this ConfigMap: {cfg_map}")
            if not opts.o.dry_run:
                cm_name = cfg_map.metadata.name
                try:
                    self.core_api.create_namespaced_config_map(
                        body=cfg_map, namespace=self.k8s_namespace
                    )
                except ApiException as e:
                    if e.status == 409:
                        self.core_api.patch_namespaced_config_map(
                            name=cm_name,
                            namespace=self.k8s_namespace,
                            body=cfg_map,
                        )
                    else:
                        raise

    def _create_external_services(self):
        """Create k8s Services for external-services declared in the spec.

        For host mode: ExternalName Service (DNS CNAME).
        For ip mode: headless Service + Endpoints with static IP.
        For selector mode: headless Service + Endpoints with pod IPs
        discovered from the target namespace.
        """
        resources = self.cluster_info.get_external_service_resources()
        ext_services = self.cluster_info.spec.get_external_services()

        for resource in resources:
            if opts.o.dry_run:
                print(
                    f"Dry run: would create external service: {resource.metadata.name}"
                )
                continue

            svc_name = resource.metadata.name
            try:
                self.core_api.create_namespaced_service(
                    body=resource, namespace=self.k8s_namespace
                )
                print(f"Created external service '{svc_name}'")
            except ApiException as e:
                if e.status == 409:
                    self.core_api.replace_namespaced_service(
                        name=svc_name,
                        namespace=self.k8s_namespace,
                        body=resource,
                    )
                    print(f"Updated external service '{svc_name}'")
                else:
                    raise

        # Create Endpoints for ip-mode services (static IP)
        for name, svc_config in ext_services.items():
            if "ip" not in svc_config:
                continue
            if opts.o.dry_run:
                continue

            ip = svc_config["ip"]
            port = svc_config.get("port", 443)

            endpoints = client.V1Endpoints(
                metadata=client.V1ObjectMeta(
                    name=name,
                    labels=self.cluster_info._stack_labels(),
                ),
                subsets=[
                    client.V1EndpointSubset(
                        addresses=[client.V1EndpointAddress(ip=ip)],
                        ports=[
                            client.CoreV1EndpointPort(port=port, name=f"port-{port}")
                        ],
                    )
                ],
            )

            try:
                self.core_api.create_namespaced_endpoints(
                    body=endpoints, namespace=self.k8s_namespace
                )
                print(f"Created endpoints for '{name}' → {ip}:{port}")
            except ApiException as e:
                if e.status == 409:
                    self.core_api.replace_namespaced_endpoints(
                        name=name,
                        namespace=self.k8s_namespace,
                        body=endpoints,
                    )
                    print(f"Updated endpoints for '{name}' → {ip}:{port}")
                else:
                    raise

        # Create Endpoints for selector-mode services
        for name, svc_config in ext_services.items():
            if "selector" not in svc_config or "namespace" not in svc_config:
                continue
            if opts.o.dry_run:
                continue

            target_ns = svc_config["namespace"]
            selector = svc_config["selector"]
            port = svc_config.get("port", 443)

            # Build label selector string from dict
            label_selector = ",".join(f"{k}={v}" for k, v in selector.items())

            # Discover pod IPs in target namespace
            pods = self.core_api.list_namespaced_pod(
                namespace=target_ns, label_selector=label_selector
            )
            pod_ips = [
                p.status.pod_ip for p in pods.items if p.status and p.status.pod_ip
            ]

            if not pod_ips:
                print(
                    f"Warning: no pods found in {target_ns} matching "
                    f"{label_selector} for external service '{name}'"
                )
                continue

            endpoints = client.V1Endpoints(
                metadata=client.V1ObjectMeta(
                    name=name,
                    labels=self.cluster_info._stack_labels(),
                ),
                subsets=[
                    client.V1EndpointSubset(
                        addresses=[client.V1EndpointAddress(ip=ip) for ip in pod_ips],
                        ports=[
                            client.CoreV1EndpointPort(port=port, name=f"port-{port}")
                        ],
                    )
                ],
            )

            try:
                self.core_api.create_namespaced_endpoints(
                    body=endpoints, namespace=self.k8s_namespace
                )
                print(f"Created endpoints for '{name}' → {pod_ips}")
            except ApiException as e:
                if e.status == 409:
                    self.core_api.replace_namespaced_endpoints(
                        name=name,
                        namespace=self.k8s_namespace,
                        body=endpoints,
                    )
                    print(f"Updated endpoints for '{name}' → {pod_ips}")
                else:
                    raise

    def _create_ca_certificates(self):
        """Create k8s Secret for CA certificates declared in the spec.

        The Secret is mounted into containers by get_deployments() in
        cluster_info.py. This method just ensures the Secret exists.
        """
        ca_secret, _, _, _ = self.cluster_info.get_ca_certificate_resources()
        if not ca_secret:
            return
        if opts.o.dry_run:
            print("Dry run: would create CA certificate secret")
            return

        secret_name = ca_secret.metadata.name
        try:
            self.core_api.create_namespaced_secret(
                body=ca_secret, namespace=self.k8s_namespace
            )
            print(f"Created CA certificate secret '{secret_name}'")
        except ApiException as e:
            if e.status == 409:
                self.core_api.replace_namespaced_secret(
                    name=secret_name,
                    namespace=self.k8s_namespace,
                    body=ca_secret,
                )
                print(f"Updated CA certificate secret '{secret_name}'")
            else:
                raise

    def _create_deployment(self):
        """Create the k8s Deployment resource (which starts pods)."""
        # Skip if there are no pods to deploy (e.g. jobs-only stacks)
        if not self.cluster_info.parsed_pod_yaml_map:
            if opts.o.debug:
                print("No pods defined, skipping Deployment creation")
            return
        # Process compose files into Deployments (one per pod file)
        # image-pull-policy from spec. Default IfNotPresent for kind (local
        # images are loaded via `kind load`), Always for production k8s.
        default_policy = "IfNotPresent" if self.is_kind() else "Always"
        pull_policy = self.cluster_info.spec.get("image-pull-policy", default_policy)
        deployments = self.cluster_info.get_deployments(image_pull_policy=pull_policy)
        for deployment in deployments:
            # Apply image overrides if provided
            if self.image_overrides:
                for container in deployment.spec.template.spec.containers:
                    if container.name in self.image_overrides:
                        container.image = self.image_overrides[container.name]
                        if opts.o.debug:
                            print(
                                f"Overriding image for {container.name}:"
                                f" {container.image}"
                            )
            # Create or update the k8s Deployment
            if opts.o.debug:
                print(f"Sending this deployment: {deployment}")
            if not opts.o.dry_run:
                name = deployment.metadata.name
                try:
                    deployment_resp = cast(
                        client.V1Deployment,
                        self.apps_api.create_namespaced_deployment(
                            body=deployment, namespace=self.k8s_namespace
                        ),
                    )
                    strategy = (
                        deployment.spec.strategy.type
                        if deployment.spec.strategy
                        else "default"
                    )
                    print(f"Created Deployment {name} (strategy: {strategy})")
                except ApiException as e:
                    if e.status == 409:
                        # Already exists — replace to ensure removed fields
                        # (volumes, mounts, env vars) are actually deleted.
                        existing = self.apps_api.read_namespaced_deployment(
                            name=name, namespace=self.k8s_namespace
                        )
                        deployment.metadata.resource_version = (
                            existing.metadata.resource_version
                        )
                        deployment_resp = cast(
                            client.V1Deployment,
                            self.apps_api.replace_namespaced_deployment(
                                name=name,
                                namespace=self.k8s_namespace,
                                body=deployment,
                            ),
                        )
                        print(f"Updated Deployment {name} (rolling update)")
                    else:
                        raise
                if opts.o.debug:
                    meta = deployment_resp.metadata
                    spec = deployment_resp.spec
                    if meta and spec and spec.template.spec:
                        containers = spec.template.spec.containers
                        img = containers[0].image if containers else None
                        print(
                            f"  {meta.namespace} {meta.name}"
                            f" gen={meta.generation} {img}"
                        )

        # Create Services (one per pod for multi-pod, or one for single-pod)
        services = self.cluster_info.get_services()
        for service in services:
            if opts.o.debug:
                print(f"Sending this service: {service}")
            if service and not opts.o.dry_run:
                svc_name = service.metadata.name
                try:
                    service_resp = self.core_api.create_namespaced_service(
                        namespace=self.k8s_namespace, body=service
                    )
                    print(f"Created Service {svc_name}")
                except ApiException as e:
                    if e.status == 409:
                        # Replace to ensure removed ports are deleted.
                        # Must preserve clusterIP (immutable) and resourceVersion.
                        existing = self.core_api.read_namespaced_service(
                            name=svc_name, namespace=self.k8s_namespace
                        )
                        service.metadata.resource_version = (
                            existing.metadata.resource_version
                        )
                        service.spec.cluster_ip = existing.spec.cluster_ip
                        service_resp = self.core_api.replace_namespaced_service(
                            name=svc_name,
                            namespace=self.k8s_namespace,
                            body=service,
                        )
                        print(f"Updated Service {svc_name}")
                    else:
                        raise
                if opts.o.debug:
                    print(f"  {service_resp}")

    def _create_jobs(self):
        # Process job compose files into k8s Jobs
        job_pull_policy = "IfNotPresent" if self.is_kind() else "Always"
        jobs = self.cluster_info.get_jobs(image_pull_policy=job_pull_policy)
        for job in jobs:
            if opts.o.debug:
                print(f"Sending this job: {job}")
            if not opts.o.dry_run:
                job_name = job.metadata.name
                try:
                    job_resp = self.batch_api.create_namespaced_job(
                        body=job, namespace=self.k8s_namespace
                    )
                    if opts.o.debug:
                        print("Job created:")
                        if job_resp.metadata:
                            print(
                                f"  {job_resp.metadata.namespace} "
                                f"{job_resp.metadata.name}"
                            )
                except ApiException as e:
                    if e.status == 409:
                        # Job already exists from a prior run. Jobs are one-
                        # shot — don't recreate on restart. Delete the Job
                        # explicitly to re-run (stop --delete-volumes also
                        # clears them via label-based cleanup).
                        print(f"Job {job_name} already exists, skipping")
                    else:
                        raise

    def _find_certificate_for_host_name(self, host_name):
        all_certificates = self.custom_obj_api.list_namespaced_custom_object(
            group="cert-manager.io",
            version="v1",
            namespace=self.k8s_namespace,
            plural="certificates",
        )

        host_parts = host_name.split(".", 1)
        host_as_wild = None
        if len(host_parts) == 2:
            host_as_wild = f"*.{host_parts[1]}"

        # TODO: resolve method deprecation below
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        fmt = "%Y-%m-%dT%H:%M:%S%z"

        # Walk over all the configured certificates.
        for cert in all_certificates["items"]:
            dns = cert["spec"]["dnsNames"]
            # Check for an exact hostname match or a wildcard match.
            if host_name in dns or host_as_wild in dns:
                status = cert.get("status", {})
                # Check the certificate date.
                if "notAfter" in status and "notBefore" in status:
                    before = datetime.strptime(status["notBefore"], fmt)
                    after = datetime.strptime(status["notAfter"], fmt)
                    if before < now < after:
                        # Check the status is Ready
                        for condition in status.get("conditions", []):
                            if "True" == condition.get(
                                "status"
                            ) and "Ready" == condition.get("type"):
                                return cert
        return None

    def _setup_cluster(self):
        """Create/reuse kind cluster, load images, ensure namespace."""
        if self.is_kind() and not self.skip_cluster_management:
            kind_config = str(
                self.deployment_dir.joinpath(constants.kind_config_filename)
            )
            actual_cluster = create_cluster(self.kind_cluster_name, kind_config)
            if actual_cluster != self.kind_cluster_name:
                self.kind_cluster_name = actual_cluster
            local_containers = self.deployment_context.stack.obj.get("containers", [])
            images_to_preload = set((self.image_overrides or {}).values()) | {
                img
                for img in self.cluster_info.image_set
                if any(c in img for c in local_containers)
            }
            images_to_preload = {
                img for img in images_to_preload if is_image_available_locally(img)
            }
            if images_to_preload:
                load_images_into_kind(self.kind_cluster_name, images_to_preload)
        elif self.is_kind():
            # --skip-cluster-management (default): cluster must already exist.
            # Without this check, connect_api() below raises a cryptic
            # kubernetes.config.ConfigException when the context is missing.
            existing = get_kind_cluster()
            if existing is None:
                raise DeployerException(
                    f"No kind cluster is running. This deployment expects "
                    f"cluster '{self.kind_cluster_name}' to exist.\n"
                    "\n"
                    "--skip-cluster-management is the default; pass "
                    "--perform-cluster-management to have laconic-so "
                    "create the cluster, or start it manually first."
                )
            if existing != self.kind_cluster_name:
                raise DeployerException(
                    f"Running kind cluster '{existing}' does not match the "
                    f"cluster-id '{self.kind_cluster_name}' in "
                    f"{self.deployment_dir}/deployment.yml.\n"
                    "\n"
                    "Fix by either:\n"
                    "  - editing deployment.yml to set "
                    f"cluster-id: {existing}, or\n"
                    "  - passing --perform-cluster-management to create a "
                    "fresh cluster (note: destroys the existing one if "
                    "names collide)."
                )
            # Mount topology applies regardless of who owns cluster
            # lifecycle — validate here too.
            kind_config = str(
                self.deployment_dir.joinpath(constants.kind_config_filename)
            )
            check_mounts_compatible(existing, kind_config)
        self.connect_api()
        self._ensure_namespace()
        caddy_image = self.cluster_info.spec.get_caddy_ingress_image()
        # Fresh-install path: gated on cluster lifecycle ownership
        # because install_ingress_for_kind also seeds caddy-system
        # (namespace, secrets restore, cert-backup CronJob).
        if self.is_kind() and not self.skip_cluster_management:
            if not is_ingress_running():
                install_ingress_for_kind(
                    self.cluster_info.spec.get_acme_email(),
                    self.cluster_info.spec.get_kind_mount_root(),
                    caddy_image=caddy_image,
                )
                wait_for_ingress_in_kind()
            if self.cluster_info.spec.get_unlimited_memlock():
                _create_runtime_class(
                    constants.high_memlock_runtime,
                    constants.high_memlock_runtime,
                )
        # Reconcile Caddy image whenever the operator explicitly set
        # it in spec, regardless of cluster lifecycle ownership —
        # --skip-cluster-management (the default) shouldn't prevent
        # a routine k8s-API-level patch of a running Deployment.
        # Spec absent => don't touch: the operator may have set the
        # image out-of-band (ansible playbook, prior explicit spec on
        # a different deployment) and a silent revert would be worse
        # than doing nothing. caddy-system is cluster-scoped, so
        # whichever deployment's spec sets the image last wins.
        if self.is_kind() and caddy_image is not None and is_ingress_running():
            if update_caddy_ingress_image(caddy_image):
                wait_for_ingress_in_kind()

    def _create_ingress(self):
        """Create or update Ingress with TLS certificate lookup."""
        http_proxy_info = self.cluster_info.spec.get_http_proxy()
        use_tls = http_proxy_info and not self.is_kind()
        certificates = None
        if use_tls:
            certificates = {}
            for proxy in http_proxy_info:
                host_name = proxy["host-name"]
                cert = self._find_certificate_for_host_name(host_name)
                if cert:
                    certificates[host_name] = cert
                    if opts.o.debug:
                        print(f"Using existing certificate for {host_name}: {cert}")

        ingress = self.cluster_info.get_ingress(
            use_tls=use_tls, certificates=certificates
        )
        if ingress:
            if opts.o.debug:
                print(f"Sending this ingress: {ingress}")
            if not opts.o.dry_run:
                ing_name = ingress.metadata.name
                try:
                    self.networking_api.create_namespaced_ingress(
                        namespace=self.k8s_namespace, body=ingress
                    )
                    print(f"Created Ingress {ing_name}")
                except ApiException as e:
                    if e.status == 409:
                        existing = self.networking_api.read_namespaced_ingress(
                            name=ing_name, namespace=self.k8s_namespace
                        )
                        ingress.metadata.resource_version = (
                            existing.metadata.resource_version
                        )
                        self.networking_api.replace_namespaced_ingress(
                            name=ing_name,
                            namespace=self.k8s_namespace,
                            body=ingress,
                        )
                        print(f"Updated Ingress {ing_name}")
                    else:
                        raise
        else:
            if opts.o.debug:
                print("No ingress configured")

    def _create_nodeports(self):
        """Create or update NodePort services."""
        nodeports: List[client.V1Service] = self.cluster_info.get_nodeports()
        for nodeport in nodeports:
            if opts.o.debug:
                print(f"Sending this nodeport: {nodeport}")
            if not opts.o.dry_run:
                np_name = nodeport.metadata.name
                try:
                    self.core_api.create_namespaced_service(
                        namespace=self.k8s_namespace, body=nodeport
                    )
                except ApiException as e:
                    if e.status == 409:
                        existing = self.core_api.read_namespaced_service(
                            name=np_name, namespace=self.k8s_namespace
                        )
                        nodeport.metadata.resource_version = (
                            existing.metadata.resource_version
                        )
                        nodeport.spec.cluster_ip = existing.spec.cluster_ip
                        self.core_api.replace_namespaced_service(
                            name=np_name,
                            namespace=self.k8s_namespace,
                            body=nodeport,
                        )
                    else:
                        raise

    def up(
        self,
        detach,
        skip_cluster_management,
        services,
        image_overrides=None,
        force_recreate=False,
    ):
        # TODO: honor force_recreate by stamping the
        # kubectl.kubernetes.io/restartedAt annotation on managed
        # Deployments so a rollout occurs even when the manifest is
        # unchanged. Today this method is a no-op for that flag.
        # Tracked separately from the compose-side fix.
        # Merge spec-level image overrides with CLI overrides
        spec_overrides = self.cluster_info.spec.get("image-overrides", {})
        if spec_overrides:
            if image_overrides:
                spec_overrides.update(image_overrides)  # CLI wins
            image_overrides = spec_overrides
        self.image_overrides = image_overrides
        self.skip_cluster_management = skip_cluster_management
        if not opts.o.dry_run:
            self._setup_cluster()
        else:
            print("Dry run mode enabled, skipping k8s API connect")

        # Create registry secret if configured
        from stack_orchestrator.deploy.deployment_create import create_registry_secret

        create_registry_secret(
            self.cluster_info.spec, self.cluster_info.app_name, self.k8s_namespace
        )

        self._create_volume_data()
        self._create_external_services()
        self._create_ca_certificates()
        self._create_deployment()
        self._create_jobs()
        self._create_ingress()
        self._create_nodeports()

        # Call start() hooks — stacks can create additional k8s resources
        if self.deployment_context:
            from stack_orchestrator.deploy.deployment_create import (
                call_stack_deploy_start,
            )

            call_stack_deploy_start(self.deployment_context)

    def down(self, timeout, volumes, skip_cluster_management, delete_namespace=False):
        """Tear down stack-labeled resources. Phases:

        1. Delete namespaced resources (if namespace still exists).
        2. Delete cluster-scoped PVs (if --delete-volumes, regardless of (1)).
        3. Wait for everything we triggered to actually be gone.
        4. Optionally delete the namespace itself (--delete-namespace).
        5. Optionally destroy the kind cluster (--perform-cluster-management).

        Steps 1-3 scope cleanup to a single stack via app.kubernetes.io/stack,
        so multiple stacks sharing a namespace tear down independently.
        """
        self.skip_cluster_management = skip_cluster_management
        self.connect_api()

        selector = self._stack_label_selector()
        ns = self.k8s_namespace
        ns_exists = self._namespace_exists(ns)

        if ns_exists:
            self._delete_namespaced_labeled_resources(ns, selector, volumes)
        if volumes:
            self._delete_labeled_pvs(selector)
        self._wait_for_labeled_gone(
            ns, selector, delete_volumes=volumes, namespace_present=ns_exists
        )

        if delete_namespace and ns_exists:
            self._delete_namespace()
            self._wait_for_namespace_gone()

        if self.is_kind() and not self.skip_cluster_management:
            destroy_cluster(self.kind_cluster_name)

    def _stack_label_selector(self) -> str:
        """Selector used for stack-scoped cleanup.

        Prefer app.kubernetes.io/stack (per-stack) and fall back to the
        legacy app= label (cluster-id scoped) for deployments that predate
        the stack label.
        """
        stack_name = self.cluster_info.stack_name
        if stack_name:
            return f"app.kubernetes.io/stack={stack_name}"
        return f"app={self.cluster_info.app_name}"

    def _namespace_exists(self, namespace: str) -> bool:
        try:
            self.core_api.read_namespace(name=namespace)
            return True
        except ApiException as e:
            if e.status == 404:
                if opts.o.debug:
                    print(f"Namespace {namespace} not found")
                return False
            raise

    def _delete_namespaced_labeled_resources(
        self, namespace: str, selector: str, delete_volumes: bool
    ):
        """Delete Ingresses, Deployments, Jobs, Services, ConfigMaps,
        Secrets, Endpoints, Pods, and (if delete_volumes) PVCs in the
        namespace. Order matters: Ingresses first so external traffic
        stops, then workloads, then support objects, then Pods, then PVCs.
        """
        if opts.o.dry_run:
            print(
                f"Dry run: would delete namespaced resources in {namespace} "
                f"matching {selector}"
            )
            return

        def swallow_404(fn):
            try:
                fn()
            except ApiException as e:
                if e.status not in (404, 405):
                    raise

        # Ingresses first so external traffic stops before pods disappear.
        swallow_404(
            lambda: self.networking_api.delete_collection_namespaced_ingress(
                namespace=namespace, label_selector=selector
            )
        )
        # Deployments (owns ReplicaSets + Pods via GC).
        swallow_404(
            lambda: self.apps_api.delete_collection_namespaced_deployment(
                namespace=namespace, label_selector=selector
            )
        )
        # Jobs — propagation=Background cascades to child pods.
        swallow_404(
            lambda: self.batch_api.delete_collection_namespaced_job(
                namespace=namespace,
                label_selector=selector,
                propagation_policy="Background",
            )
        )
        # Services have no delete_collection on core_api; list + delete.
        self._list_delete_namespaced(
            namespace,
            selector,
            list_fn=self.core_api.list_namespaced_service,
            delete_fn=self.core_api.delete_namespaced_service,
        )
        # ConfigMaps, Secrets.
        swallow_404(
            lambda: self.core_api.delete_collection_namespaced_config_map(
                namespace=namespace, label_selector=selector
            )
        )
        swallow_404(
            lambda: self.core_api.delete_collection_namespaced_secret(
                namespace=namespace, label_selector=selector
            )
        )
        # Endpoints usually GC with Services, but we create a few directly
        # (external-services) that aren't owned by a Service — clean those.
        self._list_delete_namespaced(
            namespace,
            selector,
            list_fn=self.core_api.list_namespaced_endpoints,
            delete_fn=self.core_api.delete_namespaced_endpoints,
        )
        # Stray pods (owned pods are GC'd with their Deployment/Job).
        swallow_404(
            lambda: self.core_api.delete_collection_namespaced_pod(
                namespace=namespace, label_selector=selector
            )
        )
        if delete_volumes:
            swallow_404(
                lambda: self.core_api.delete_collection_namespaced_persistent_volume_claim(  # noqa: E501
                    namespace=namespace, label_selector=selector
                )
            )

    def _list_delete_namespaced(self, namespace, selector, list_fn, delete_fn):
        """List by selector and delete each item. Use for resources where
        the k8s python client lacks delete_collection (Services, Endpoints).
        """
        try:
            items = list_fn(namespace=namespace, label_selector=selector).items
        except ApiException as e:
            if e.status == 404:
                return
            raise
        for item in items:
            try:
                delete_fn(name=item.metadata.name, namespace=namespace)
            except ApiException as e:
                if e.status not in (404, 405):
                    raise

    def _delete_labeled_pvs(self, selector: str):
        """Delete cluster-scoped PVs matching the stack label."""
        if opts.o.dry_run:
            print(f"Dry run: would delete PVs matching {selector}")
            return
        try:
            pvs = self.core_api.list_persistent_volume(label_selector=selector)
        except ApiException as e:
            if opts.o.debug:
                print(f"Error listing PVs: {e}")
            return
        for pv in pvs.items:
            if opts.o.debug:
                print(f"Deleting PV: {pv.metadata.name}")
            try:
                self.core_api.delete_persistent_volume(name=pv.metadata.name)
            except ApiException as e:
                _check_delete_exception(e)

    def _wait_for_labeled_gone(
        self,
        namespace: str,
        selector: str,
        delete_volumes: bool,
        namespace_present: bool,
        timeout_seconds: int = 120,
    ):
        """Poll until every kind we triggered a delete for is gone.

        delete_collection/delete are async — finalizers (PV bound-by-PVC,
        PVC bound-by-VolumeAttachment, pod graceful shutdown) propagate
        after the API call returns. Blocking here makes down() a
        synchronous contract for callers (tests, ansible, cryovial).
        """
        import time

        listers = []
        if namespace_present:
            listers += [
                (
                    "deployment",
                    lambda: self.apps_api.list_namespaced_deployment(
                        namespace=namespace, label_selector=selector
                    ),
                ),
                (
                    "ingress",
                    lambda: self.networking_api.list_namespaced_ingress(
                        namespace=namespace, label_selector=selector
                    ),
                ),
                (
                    "job",
                    lambda: self.batch_api.list_namespaced_job(
                        namespace=namespace, label_selector=selector
                    ),
                ),
                (
                    "service",
                    lambda: self.core_api.list_namespaced_service(
                        namespace=namespace, label_selector=selector
                    ),
                ),
                (
                    "configmap",
                    lambda: self.core_api.list_namespaced_config_map(
                        namespace=namespace, label_selector=selector
                    ),
                ),
                (
                    "secret",
                    lambda: self.core_api.list_namespaced_secret(
                        namespace=namespace, label_selector=selector
                    ),
                ),
                (
                    "pod",
                    lambda: self.core_api.list_namespaced_pod(
                        namespace=namespace, label_selector=selector
                    ),
                ),
            ]
            if delete_volumes:
                listers.append(
                    (
                        "persistentvolumeclaim",
                        lambda: self.core_api.list_namespaced_persistent_volume_claim(
                            namespace=namespace, label_selector=selector
                        ),
                    )
                )
        # PVs are cluster-scoped — wait for them even when the namespace
        # is already gone (orphaned from a prior --delete-namespace).
        if delete_volumes:
            listers.append(
                (
                    "persistentvolume",
                    lambda: self.core_api.list_persistent_volume(
                        label_selector=selector
                    ),
                )
            )

        def remaining():
            out = []
            for kind, lister in listers:
                try:
                    items = lister().items
                except ApiException as e:
                    if e.status == 404:
                        continue
                    raise
                if items:
                    out.append((kind, len(items)))
            return out

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            left = remaining()
            if not left:
                return
            if opts.o.debug:
                print(f"Waiting for deletions: {left}")
            time.sleep(2)

        left = remaining()
        if left:
            print(
                f"Warning: resources still present after {timeout_seconds}s: " f"{left}"
            )

    def status(self):
        self.connect_api()
        # Call whatever API we need to get the running container list
        all_pods = self.core_api.list_pod_for_all_namespaces(watch=False)
        pods = []

        if all_pods.items:
            for p in all_pods.items:
                if p.metadata and p.metadata.name:
                    if f"{self.cluster_info.app_name}-deployment" in p.metadata.name:
                        pods.append(p)

        if not pods:
            return

        hostname = "?"
        ip = "?"
        tls = "?"
        try:
            cluster_ingress = self.cluster_info.get_ingress()
            if cluster_ingress is None or cluster_ingress.metadata is None:
                return
            ingress = cast(
                client.V1Ingress,
                self.networking_api.read_namespaced_ingress(
                    namespace=self.k8s_namespace,
                    name=cluster_ingress.metadata.name,
                ),
            )
            if not ingress.spec or not ingress.spec.tls or not ingress.spec.rules:
                return

            cert = cast(
                Dict[str, Any],
                self.custom_obj_api.get_namespaced_custom_object(
                    group="cert-manager.io",
                    version="v1",
                    namespace=self.k8s_namespace,
                    plural="certificates",
                    name=ingress.spec.tls[0].secret_name,
                ),
            )

            hostname = ingress.spec.rules[0].host
            if ingress.status and ingress.status.load_balancer:
                lb_ingress = ingress.status.load_balancer.ingress
                if lb_ingress:
                    ip = lb_ingress[0].ip or "?"
            cert_status = cert.get("status", {})
            tls = "notBefore: %s; notAfter: %s; names: %s" % (
                cert_status.get("notBefore", "?"),
                cert_status.get("notAfter", "?"),
                ingress.spec.tls[0].hosts,
            )
        except:  # noqa: E722
            pass

        print("Ingress:")
        print("\tHostname:", hostname)
        print("\tIP:", ip)
        print("\tTLS:", tls)
        print("")
        print("Pods:")

        for p in pods:
            if not p.metadata:
                continue
            ns = p.metadata.namespace
            name = p.metadata.name
            if p.metadata.deletion_timestamp:
                ts = p.metadata.deletion_timestamp
                print(f"\t{ns}/{name}: Terminating ({ts})")
            else:
                ts = p.metadata.creation_timestamp
                print(f"\t{ns}/{name}: Running ({ts})")

    def ps(self):
        self.connect_api()
        pods = self.core_api.list_pod_for_all_namespaces(watch=False)

        ret = []

        for p in pods.items:
            if f"{self.cluster_info.app_name}-deployment" in p.metadata.name:
                pod_ip = p.status.pod_ip
                ports = AttrDict()
                for c in p.spec.containers:
                    if c.ports:
                        for prt in c.ports:
                            ports[str(prt.container_port)] = [
                                AttrDict(
                                    {"HostIp": pod_ip, "HostPort": prt.container_port}
                                )
                            ]

                ret.append(
                    AttrDict(
                        {
                            "id": f"{p.metadata.namespace}/{p.metadata.name}",
                            "name": p.metadata.name,
                            "namespace": p.metadata.namespace,
                            "network_settings": AttrDict({"ports": ports}),
                        }
                    )
                )

        return ret

    def port(self, service, private_port):
        # Since we handle the port mapping, need to figure out where this comes from
        # Also look into whether it makes sense to get ports for k8s
        pass

    def execute(self, service_name, command, tty, envs):
        # Call the API to execute a command in a running container
        pass

    def logs(self, services, tail, follow, stream):
        self.connect_api()
        pods = pods_in_deployment(
            self.core_api, self.cluster_info.app_name, namespace=self.k8s_namespace
        )
        if len(pods) > 1:
            print("Warning: more than one pod in the deployment")
        if len(pods) == 0:
            log_data = "******* Pods not running ********\n"
        else:
            k8s_pod_name = pods[0]
            containers = containers_in_pod(
                self.core_api, k8s_pod_name, namespace=self.k8s_namespace
            )
            # If pod not started, logs request below will throw an exception
            try:
                log_data = ""
                for container in containers:
                    container_log = self.core_api.read_namespaced_pod_log(
                        k8s_pod_name, namespace=self.k8s_namespace, container=container
                    )
                    container_log_lines = container_log.splitlines()
                    for line in container_log_lines:
                        log_data += f"{container}: {line}\n"
            except ApiException as e:
                if opts.o.debug:
                    print(f"Error from read_namespaced_pod_log: {e}")
                log_data = "******* No logs available ********\n"
        return log_stream_from_string(log_data)

    def update_envs(self):
        if not self.cluster_info.parsed_pod_yaml_map:
            if opts.o.debug:
                print("No pods defined, skipping update")
            return
        self.connect_api()
        ref_deployments = self.cluster_info.get_deployments()
        for ref_deployment in ref_deployments:
            if not ref_deployment or not ref_deployment.metadata:
                continue
            ref_name = ref_deployment.metadata.name
            if not ref_name:
                continue

            deployment = cast(
                client.V1Deployment,
                self.apps_api.read_namespaced_deployment(
                    name=ref_name, namespace=self.k8s_namespace
                ),
            )
            if not deployment.spec or not deployment.spec.template:
                continue
            template_spec = deployment.spec.template.spec
            if not template_spec or not template_spec.containers:
                continue

            ref_spec = ref_deployment.spec
            if ref_spec and ref_spec.template and ref_spec.template.spec:
                ref_containers = ref_spec.template.spec.containers
                if ref_containers:
                    new_env = ref_containers[0].env
                    for container in template_spec.containers:
                        old_env = container.env
                        if old_env != new_env:
                            container.env = new_env

            template_meta = deployment.spec.template.metadata
            if template_meta:
                template_meta.annotations = {
                    "kubectl.kubernetes.io/restartedAt": datetime.utcnow()
                    .replace(tzinfo=timezone.utc)
                    .isoformat()
                }

            self.apps_api.patch_namespaced_deployment(
                name=ref_name,
                namespace=self.k8s_namespace,
                body=deployment,
            )

    def run(
        self,
        image: str,
        command=None,
        user=None,
        volumes=None,
        entrypoint=None,
        env={},
        ports=[],
        detach=False,
    ):
        # We need to figure out how to do this -- check why we're being called first
        pass

    def run_job(self, job_name: str, helm_release: Optional[str] = None):
        if not opts.o.dry_run:
            # Check if this is a helm-based deployment
            chart_dir = self.deployment_dir / "chart"
            if chart_dir.exists():
                from stack_orchestrator.deploy.k8s.helm.job_runner import run_helm_job

                # Run the job using the helm job runner
                run_helm_job(
                    chart_dir=chart_dir,
                    job_name=job_name,
                    release=helm_release,
                    namespace=self.k8s_namespace,
                    timeout=600,
                    verbose=opts.o.verbose,
                )
            else:
                # Non-Helm path: create job from ClusterInfo
                self.connect_api()
                job_pull_policy = "IfNotPresent" if self.is_kind() else "Always"
                jobs = self.cluster_info.get_jobs(image_pull_policy=job_pull_policy)
                # Find the matching job by name
                target_name = f"{self.cluster_info.app_name}-job-{job_name}"
                matched_job = None
                for job in jobs:
                    if job.metadata and job.metadata.name == target_name:
                        matched_job = job
                        break
                if matched_job is None:
                    raise Exception(
                        f"Job '{job_name}' not found. Available jobs: "
                        f"{[j.metadata.name for j in jobs if j.metadata]}"
                    )
                if opts.o.debug:
                    print(f"Creating job: {target_name}")
                self.batch_api.create_namespaced_job(
                    body=matched_job, namespace=self.k8s_namespace
                )

    def is_kind(self):
        return self.type == "k8s-kind"


class K8sDeployerConfigGenerator(DeployerConfigGenerator):
    type: str

    def __init__(self, type: str, deployment_context) -> None:
        self.type = type
        self.deployment_context = deployment_context
        super().__init__()

    def generate(self, deployment_dir: Path):
        # No need to do this for the remote k8s case
        if self.type == "k8s-kind":
            # Generate high-memlock-spec.json if unlimited_memlock is enabled.
            # Must be done before generate_kind_config() which references it.
            if self.deployment_context.spec.get_unlimited_memlock():
                spec_content = generate_high_memlock_spec_json()
                spec_file = deployment_dir.joinpath(
                    constants.high_memlock_spec_filename
                )
                if opts.o.debug:
                    print(
                        f"Creating high-memlock spec for unlimited memlock: {spec_file}"
                    )
                with open(spec_file, "w") as output_file:
                    output_file.write(spec_content)

            # Check the file isn't already there
            # Get the config file contents
            content = generate_kind_config(deployment_dir, self.deployment_context)
            if opts.o.debug:
                print(f"kind config is: {content}")
            config_file = deployment_dir.joinpath(constants.kind_config_filename)
            # Write the file
            with open(config_file, "w") as output_file:
                output_file.write(content)
