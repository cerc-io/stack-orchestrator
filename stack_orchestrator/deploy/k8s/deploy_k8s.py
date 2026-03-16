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
from stack_orchestrator.deploy.deployer import Deployer, DeployerConfigGenerator
from stack_orchestrator.deploy.k8s.helpers import (
    create_cluster,
    destroy_cluster,
    load_images_into_kind,
)
from stack_orchestrator.deploy.k8s.helpers import (
    install_ingress_for_kind,
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
        self.k8s_namespace = "default"  # Will be overridden below if context exists
        # TODO: workaround pending refactoring above to cope with being
        # created with a null deployment_context
        if deployment_context is None:
            return
        self.deployment_dir = deployment_context.deployment_dir
        self.deployment_context = deployment_context
        self.kind_cluster_name = deployment_context.spec.get_kind_cluster_name() or compose_project_name
        # Use spec namespace if provided, otherwise derive from cluster-id
        self.k8s_namespace = deployment_context.spec.get_namespace() or f"laconic-{compose_project_name}"
        self.cluster_info = ClusterInfo()
        # stack.name may be an absolute path (from spec "stack:" key after
        # path resolution). Extract just the directory basename for labels.
        raw_name = deployment_context.stack.name if deployment_context else ""
        stack_name = Path(raw_name).name if raw_name else ""
        self.cluster_info.int(
            compose_files,
            compose_env_file,
            compose_project_name,
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
        """Create the deployment namespace if it doesn't exist."""
        if opts.o.dry_run:
            print(f"Dry run: would create namespace {self.k8s_namespace}")
            return
        try:
            self.core_api.read_namespace(name=self.k8s_namespace)
            if opts.o.debug:
                print(f"Namespace {self.k8s_namespace} already exists")
        except ApiException as e:
            if e.status == 404:
                # Create the namespace
                ns = client.V1Namespace(
                    metadata=client.V1ObjectMeta(
                        name=self.k8s_namespace,
                        labels={"app": self.cluster_info.app_name},
                    )
                )
                self.core_api.create_namespace(body=ns)
                if opts.o.debug:
                    print(f"Created namespace {self.k8s_namespace}")
            else:
                raise

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
                    name=job.metadata.name, namespace=ns,
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

    def _create_volume_data(self):
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
                        if opts.o.debug:
                            print("PVs already present:")
                            print(f"{pv_resp}")
                        continue
                except:  # noqa: E722
                    pass

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
                except:  # noqa: E722
                    pass

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
                cfg_rsp = self.core_api.create_namespaced_config_map(
                    body=cfg_map, namespace=self.k8s_namespace
                )
                if opts.o.debug:
                    print("ConfigMap created:")
                    print(f"{cfg_rsp}")

    def _create_deployment(self):
        # Skip if there are no pods to deploy (e.g. jobs-only stacks)
        if not self.cluster_info.parsed_pod_yaml_map:
            if opts.o.debug:
                print("No pods defined, skipping Deployment creation")
            return
        # Process compose files into a Deployment
        deployment = self.cluster_info.get_deployment(
            image_pull_policy=None if self.is_kind() else "Always"
        )
        # Create the k8s objects
        if opts.o.debug:
            print(f"Sending this deployment: {deployment}")
        if not opts.o.dry_run:
            deployment_resp = cast(
                client.V1Deployment,
                self.apps_api.create_namespaced_deployment(
                    body=deployment, namespace=self.k8s_namespace
                ),
            )
            if opts.o.debug:
                print("Deployment created:")
                meta = deployment_resp.metadata
                spec = deployment_resp.spec
                if meta and spec and spec.template.spec:
                    ns = meta.namespace
                    name = meta.name
                    gen = meta.generation
                    containers = spec.template.spec.containers
                    img = containers[0].image if containers else None
                    print(f"{ns} {name} {gen} {img}")

        service = self.cluster_info.get_service()
        if opts.o.debug:
            print(f"Sending this service: {service}")
        if service and not opts.o.dry_run:
            service_resp = self.core_api.create_namespaced_service(
                namespace=self.k8s_namespace, body=service
            )
            if opts.o.debug:
                print("Service created:")
                print(f"{service_resp}")

    def _create_jobs(self):
        # Process job compose files into k8s Jobs
        jobs = self.cluster_info.get_jobs(
            image_pull_policy=None if self.is_kind() else "Always"
        )
        for job in jobs:
            if opts.o.debug:
                print(f"Sending this job: {job}")
            if not opts.o.dry_run:
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

    def up(self, detach, skip_cluster_management, services):
        self.skip_cluster_management = skip_cluster_management
        if not opts.o.dry_run:
            if self.is_kind() and not self.skip_cluster_management:
                # Create the kind cluster (or reuse existing one)
                kind_config = str(
                    self.deployment_dir.joinpath(constants.kind_config_filename)
                )
                actual_cluster = create_cluster(self.kind_cluster_name, kind_config)
                if actual_cluster != self.kind_cluster_name:
                    # An existing cluster was found, use it instead
                    self.kind_cluster_name = actual_cluster
                # Only load locally-built images into kind
                # Registry images (docker.io, ghcr.io, etc.) will be pulled by k8s
                local_containers = self.deployment_context.stack.obj.get(
                    "containers", []
                )
                if local_containers:
                    # Filter image_set to only images matching local containers
                    local_images = {
                        img
                        for img in self.cluster_info.image_set
                        if any(c in img for c in local_containers)
                    }
                    if local_images:
                        load_images_into_kind(self.kind_cluster_name, local_images)
                # Note: if no local containers defined, all images come from registries
            self.connect_api()
            # Create deployment-specific namespace for resource isolation
            self._ensure_namespace()
            if self.is_kind() and not self.skip_cluster_management:
                # Configure ingress controller (not installed by default in kind)
                # Skip if already running (idempotent for shared cluster)
                if not is_ingress_running():
                    install_ingress_for_kind(self.cluster_info.spec.get_acme_email())
                    # Wait for ingress to start
                    # (deployment provisioning will fail unless this is done)
                    wait_for_ingress_in_kind()
                # Create RuntimeClass if unlimited_memlock is enabled
                if self.cluster_info.spec.get_unlimited_memlock():
                    _create_runtime_class(
                        constants.high_memlock_runtime,
                        constants.high_memlock_runtime,
                    )

        else:
            print("Dry run mode enabled, skipping k8s API connect")

        # Create registry secret if configured
        from stack_orchestrator.deploy.deployment_create import create_registry_secret

        create_registry_secret(self.cluster_info.spec, self.cluster_info.app_name)

        self._create_volume_data()
        self._create_deployment()
        self._create_jobs()

        http_proxy_info = self.cluster_info.spec.get_http_proxy()
        # Note: we don't support tls for kind (enabling tls causes errors)
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
                ingress_resp = self.networking_api.create_namespaced_ingress(
                    namespace=self.k8s_namespace, body=ingress
                )
                if opts.o.debug:
                    print("Ingress created:")
                    print(f"{ingress_resp}")
        else:
            if opts.o.debug:
                print("No ingress configured")

        nodeports: List[client.V1Service] = self.cluster_info.get_nodeports()
        for nodeport in nodeports:
            if opts.o.debug:
                print(f"Sending this nodeport: {nodeport}")
            if not opts.o.dry_run:
                nodeport_resp = self.core_api.create_namespaced_service(
                    namespace=self.k8s_namespace, body=nodeport
                )
                if opts.o.debug:
                    print("NodePort created:")
                    print(f"{nodeport_resp}")

        # Call start() hooks — stacks can create additional k8s resources
        if self.deployment_context:
            from stack_orchestrator.deploy.deployment_create import call_stack_deploy_start
            call_stack_deploy_start(self.deployment_context)

    def down(self, timeout, volumes, skip_cluster_management):
        self.skip_cluster_management = skip_cluster_management
        self.connect_api()

        app_label = f"app={self.cluster_info.app_name}"

        # PersistentVolumes are cluster-scoped (not namespaced), so delete by label
        if volumes:
            try:
                pvs = self.core_api.list_persistent_volume(
                    label_selector=app_label
                )
                for pv in pvs.items:
                    if opts.o.debug:
                        print(f"Deleting PV: {pv.metadata.name}")
                    try:
                        self.core_api.delete_persistent_volume(name=pv.metadata.name)
                    except ApiException as e:
                        _check_delete_exception(e)
            except ApiException as e:
                if opts.o.debug:
                    print(f"Error listing PVs: {e}")

        # When namespace is explicitly set in the spec, it may be shared with
        # other stacks — delete only this stack's resources by label.
        # Otherwise the namespace is owned by this deployment, delete it entirely.
        shared_namespace = self.deployment_context.spec.get_namespace() is not None
        if shared_namespace:
            self._delete_resources_by_label(app_label, volumes)
        else:
            self._delete_namespace()

        if self.is_kind() and not self.skip_cluster_management:
            # Destroy the kind cluster
            destroy_cluster(self.kind_cluster_name)

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
        pods = pods_in_deployment(self.core_api, self.cluster_info.app_name, namespace=self.k8s_namespace)
        if len(pods) > 1:
            print("Warning: more than one pod in the deployment")
        if len(pods) == 0:
            log_data = "******* Pods not running ********\n"
        else:
            k8s_pod_name = pods[0]
            containers = containers_in_pod(self.core_api, k8s_pod_name, namespace=self.k8s_namespace)
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

    def update(self):
        if not self.cluster_info.parsed_pod_yaml_map:
            if opts.o.debug:
                print("No pods defined, skipping update")
            return
        self.connect_api()
        ref_deployment = self.cluster_info.get_deployment()
        if not ref_deployment or not ref_deployment.metadata:
            return
        ref_name = ref_deployment.metadata.name
        if not ref_name:
            return

        deployment = cast(
            client.V1Deployment,
            self.apps_api.read_namespaced_deployment(
                name=ref_name, namespace=self.k8s_namespace
            ),
        )
        if not deployment.spec or not deployment.spec.template:
            return
        template_spec = deployment.spec.template.spec
        if not template_spec or not template_spec.containers:
            return

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
                jobs = self.cluster_info.get_jobs(
                    image_pull_policy=None if self.is_kind() else "Always"
                )
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
