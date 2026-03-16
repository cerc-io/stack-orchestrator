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

import os
import base64

from kubernetes import client
from typing import Any, List, Optional, Set

from stack_orchestrator.opts import opts
from stack_orchestrator.util import env_var_map_from_file
from stack_orchestrator.deploy.k8s.helpers import (
    named_volumes_from_pod_files,
    volume_mounts_for_service,
    volumes_for_pod_files,
)
from stack_orchestrator.deploy.k8s.helpers import get_kind_pv_bind_mount_path
from stack_orchestrator.deploy.k8s.helpers import (
    envs_from_environment_variables_map,
    envs_from_compose_file,
    merge_envs,
    translate_sidecar_service_names,
)
from stack_orchestrator.deploy.deploy_util import (
    parsed_pod_files_map_from_file_names,
    images_for_deployment,
)
from stack_orchestrator.deploy.deploy_types import DeployEnvVars
from stack_orchestrator.deploy.spec import Spec, Resources, ResourceLimits
from stack_orchestrator.deploy.images import remote_tag_for_image_unique

DEFAULT_VOLUME_RESOURCES = Resources({"reservations": {"storage": "2Gi"}})

DEFAULT_CONTAINER_RESOURCES = Resources(
    {
        "reservations": {"cpus": "1.0", "memory": "2000M"},
        "limits": {"cpus": "4.0", "memory": "8000M"},
    }
)


def to_k8s_resource_requirements(resources: Resources) -> client.V1ResourceRequirements:
    def to_dict(limits: Optional[ResourceLimits]):
        if not limits:
            return None

        ret = {}
        if limits.cpus:
            ret["cpu"] = str(limits.cpus)
        if limits.memory:
            ret["memory"] = f"{int(limits.memory / (1000 * 1000))}M"
        if limits.storage:
            ret["storage"] = f"{int(limits.storage / (1000 * 1000))}M"
        return ret

    return client.V1ResourceRequirements(
        requests=to_dict(resources.reservations), limits=to_dict(resources.limits)
    )


class ClusterInfo:
    parsed_pod_yaml_map: Any
    parsed_job_yaml_map: Any
    image_set: Set[str] = set()
    app_name: str
    stack_name: str
    environment_variables: DeployEnvVars
    spec: Spec

    def __init__(self) -> None:
        self.parsed_job_yaml_map = {}

    def int(
        self,
        pod_files: List[str],
        compose_env_file,
        deployment_name,
        spec: Spec,
        stack_name="",
    ):
        self.parsed_pod_yaml_map = parsed_pod_files_map_from_file_names(pod_files)
        # Find the set of images in the pods
        self.image_set = images_for_deployment(pod_files)
        # Filter out None values from env file
        env_vars = {
            k: v for k, v in env_var_map_from_file(compose_env_file).items() if v
        }
        self.environment_variables = DeployEnvVars(env_vars)
        self.app_name = deployment_name
        self.stack_name = stack_name
        self.spec = spec
        if opts.o.debug:
            print(f"Env vars: {self.environment_variables.map}")

    def init_jobs(self, job_files: List[str]):
        """Initialize parsed job YAML map from job compose files."""
        self.parsed_job_yaml_map = parsed_pod_files_map_from_file_names(job_files)
        if opts.o.debug:
            print(f"Parsed job yaml map: {self.parsed_job_yaml_map}")

    def _all_named_volumes(self) -> list:
        """Return named volumes from both pod and job compose files."""
        volumes = named_volumes_from_pod_files(self.parsed_pod_yaml_map)
        volumes.extend(named_volumes_from_pod_files(self.parsed_job_yaml_map))
        return volumes

    def get_nodeports(self):
        nodeports = []
        for pod_name in self.parsed_pod_yaml_map:
            pod = self.parsed_pod_yaml_map[pod_name]
            services = pod["services"]
            for service_name in services:
                service_info = services[service_name]
                if "ports" in service_info:
                    for raw_port in [str(p) for p in service_info["ports"]]:
                        if opts.o.debug:
                            print(f"service port: {raw_port}")
                        # Parse protocol suffix (e.g., "8001/udp" -> port=8001,
                        # protocol=UDP)
                        protocol = "TCP"
                        port_str = raw_port
                        if "/" in raw_port:
                            port_str, proto = raw_port.rsplit("/", 1)
                            protocol = proto.upper()
                        if ":" in port_str:
                            parts = port_str.split(":")
                            if len(parts) != 2:
                                raise Exception(f"Invalid port definition: {raw_port}")
                            node_port = int(parts[0])
                            pod_port = int(parts[1])
                        else:
                            node_port = None
                            pod_port = int(port_str)
                        service = client.V1Service(
                            metadata=client.V1ObjectMeta(
                                name=(
                                    f"{self.app_name}-nodeport-"
                                    f"{pod_port}-{protocol.lower()}"
                                ),
                                labels={"app": self.app_name},
                            ),
                            spec=client.V1ServiceSpec(
                                type="NodePort",
                                ports=[
                                    client.V1ServicePort(
                                        port=pod_port,
                                        target_port=pod_port,
                                        node_port=node_port,
                                        protocol=protocol,
                                    )
                                ],
                                selector={"app": self.app_name},
                            ),
                        )
                        nodeports.append(service)
        return nodeports

    def get_ingress(
        self, use_tls=False, certificates=None, cluster_issuer="letsencrypt-prod"
    ):
        # No ingress for a deployment that has no http-proxy defined, for now
        http_proxy_info_list = self.spec.get_http_proxy()
        ingress = None
        if http_proxy_info_list:
            rules = []
            tls = [] if use_tls else None

            for http_proxy_info in http_proxy_info_list:
                if opts.o.debug:
                    print(f"http-proxy: {http_proxy_info}")
                host_name = http_proxy_info["host-name"]
                certificate = (certificates or {}).get(host_name)

                if use_tls:
                    tls.append(
                        client.V1IngressTLS(
                            hosts=certificate["spec"]["dnsNames"]
                            if certificate
                            else [host_name],
                            secret_name=certificate["spec"]["secretName"]
                            if certificate
                            else f"{self.app_name}-{host_name}-tls",
                        )
                    )

                paths = []
                for route in http_proxy_info["routes"]:
                    path = route["path"]
                    proxy_to = route["proxy-to"]
                    if opts.o.debug:
                        print(f"proxy config: {path} -> {proxy_to}")
                    # proxy_to has the form <service>:<port>
                    proxy_to_port = int(proxy_to.split(":")[1])
                    paths.append(
                        client.V1HTTPIngressPath(
                            path_type="Prefix",
                            path=path,
                            backend=client.V1IngressBackend(
                                service=client.V1IngressServiceBackend(
                                    # TODO: this looks wrong
                                    name=f"{self.app_name}-service",
                                    # TODO: pull port number from the service
                                    port=client.V1ServiceBackendPort(
                                        number=proxy_to_port
                                    ),
                                )
                            ),
                        )
                    )
                rules.append(
                    client.V1IngressRule(
                        host=host_name,
                        http=client.V1HTTPIngressRuleValue(paths=paths),
                    )
                )

            spec = client.V1IngressSpec(tls=tls, rules=rules)

            ingress_annotations = {
                "kubernetes.io/ingress.class": "caddy",
            }
            if not certificates:
                ingress_annotations["cert-manager.io/cluster-issuer"] = cluster_issuer

            ingress = client.V1Ingress(
                metadata=client.V1ObjectMeta(
                    name=f"{self.app_name}-ingress",
                    labels={"app": self.app_name},
                    annotations=ingress_annotations,
                ),
                spec=spec,
            )
        return ingress

    # TODO: suppoprt multiple services
    def get_service(self):
        # Collect all ports from http-proxy routes
        ports_set = set()
        http_proxy_list = self.spec.get_http_proxy()
        if http_proxy_list:
            for http_proxy in http_proxy_list:
                for route in http_proxy.get("routes", []):
                    proxy_to = route.get("proxy-to", "")
                    if ":" in proxy_to:
                        port = int(proxy_to.split(":")[1])
                        ports_set.add(port)
                        if opts.o.debug:
                            print(f"http-proxy route port: {port}")

        if not ports_set:
            return None

        service_ports = [
            client.V1ServicePort(port=p, target_port=p, name=f"port-{p}")
            for p in sorted(ports_set)
        ]

        service = client.V1Service(
            metadata=client.V1ObjectMeta(
                name=f"{self.app_name}-service",
                labels={"app": self.app_name},
            ),
            spec=client.V1ServiceSpec(
                type="ClusterIP",
                ports=service_ports,
                selector={"app": self.app_name},
            ),
        )
        return service

    def get_pvcs(self):
        result = []
        spec_volumes = self.spec.get_volumes()
        named_volumes = self._all_named_volumes()
        global_resources = self.spec.get_volume_resources()
        if not global_resources:
            global_resources = DEFAULT_VOLUME_RESOURCES
        if opts.o.debug:
            print(f"Spec Volumes: {spec_volumes}")
            print(f"Named Volumes: {named_volumes}")
            print(f"Resources: {global_resources}")
        for volume_name, volume_path in spec_volumes.items():
            if volume_name not in named_volumes:
                if opts.o.debug:
                    print(f"{volume_name} not in pod files")
                continue

            # Per-volume resources override global, which overrides default.
            vol_resources = (
                self.spec.get_volume_resources_for(volume_name) or global_resources
            )

            labels = {
                "app": self.app_name,
                "volume-label": f"{self.app_name}-{volume_name}",
            }
            if volume_path:
                storage_class_name = "manual"
                k8s_volume_name = f"{self.app_name}-{volume_name}"
            else:
                # These will be auto-assigned.
                storage_class_name = None
                k8s_volume_name = None

            spec = client.V1PersistentVolumeClaimSpec(
                access_modes=["ReadWriteOnce"],
                storage_class_name=storage_class_name,
                resources=to_k8s_resource_requirements(vol_resources),
                volume_name=k8s_volume_name,
            )
            pvc = client.V1PersistentVolumeClaim(
                metadata=client.V1ObjectMeta(
                    name=f"{self.app_name}-{volume_name}", labels=labels
                ),
                spec=spec,
            )
            result.append(pvc)
        return result

    def get_configmaps(self):
        result = []
        spec_configmaps = self.spec.get_configmaps()
        named_volumes = self._all_named_volumes()
        for cfg_map_name, cfg_map_path in spec_configmaps.items():
            if cfg_map_name not in named_volumes:
                if opts.o.debug:
                    print(f"{cfg_map_name} not in pod files")
                continue

            if not cfg_map_path.startswith("/") and self.spec.file_path is not None:
                cfg_map_path = os.path.join(
                    os.path.dirname(str(self.spec.file_path)), cfg_map_path
                )

            # Read in all the files at a single-level of the directory.
            # This mimics the behavior of
            # `kubectl create configmap foo --from-file=/path/to/dir`
            data = {}
            for f in os.listdir(cfg_map_path):
                full_path = os.path.join(cfg_map_path, f)
                if os.path.isfile(full_path):
                    data[f] = base64.b64encode(open(full_path, "rb").read()).decode(
                        "ASCII"
                    )

            spec = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(
                    name=f"{self.app_name}-{cfg_map_name}",
                    labels={"app": self.app_name, "configmap-label": cfg_map_name},
                ),
                binary_data=data,
            )
            result.append(spec)
        return result

    def get_pvs(self):
        result = []
        spec_volumes = self.spec.get_volumes()
        named_volumes = self._all_named_volumes()
        global_resources = self.spec.get_volume_resources()
        if not global_resources:
            global_resources = DEFAULT_VOLUME_RESOURCES
        for volume_name, volume_path in spec_volumes.items():
            # We only need to create a volume if it is fully qualified HostPath.
            # Otherwise, we create the PVC and expect the node to allocate the volume
            # for us.
            if not volume_path:
                if opts.o.debug:
                    print(
                        f"{volume_name} does not require an explicit "
                        "PersistentVolume, since it is not a bind-mount."
                    )
                continue

            if volume_name not in named_volumes:
                if opts.o.debug:
                    print(f"{volume_name} not in pod files")
                continue

            if not os.path.isabs(volume_path):
                # For k8s-kind, allow relative paths:
                # - PV uses /mnt/{volume_name} (path inside kind node)
                # - extraMounts resolve the relative path to Docker Host
                if not self.spec.is_kind_deployment():
                    print(
                        f"WARNING: {volume_name}:{volume_path} is not absolute, "
                        "cannot bind volume."
                    )
                    continue

            vol_resources = (
                self.spec.get_volume_resources_for(volume_name) or global_resources
            )
            if self.spec.is_kind_deployment():
                host_path = client.V1HostPathVolumeSource(
                    path=get_kind_pv_bind_mount_path(volume_name)
                )
            else:
                host_path = client.V1HostPathVolumeSource(path=volume_path)
            spec = client.V1PersistentVolumeSpec(
                storage_class_name="manual",
                access_modes=["ReadWriteOnce"],
                capacity=to_k8s_resource_requirements(vol_resources).requests,
                host_path=host_path,
            )
            pv = client.V1PersistentVolume(
                metadata=client.V1ObjectMeta(
                    name=f"{self.app_name}-{volume_name}",
                    labels={
                        "app": self.app_name,
                        "volume-label": f"{self.app_name}-{volume_name}",
                    },
                ),
                spec=spec,
            )
            result.append(pv)
        return result

    def _any_service_has_host_network(self):
        for pod_name in self.parsed_pod_yaml_map:
            pod = self.parsed_pod_yaml_map[pod_name]
            for svc in pod.get("services", {}).values():
                if svc.get("network_mode") == "host":
                    return True
        return False

    def _resolve_container_resources(
        self, container_name: str, service_info: dict, global_resources: Resources
    ) -> Resources:
        """Resolve resources for a container using layered priority.

        Priority: spec per-container > compose deploy.resources
        > spec global > DEFAULT
        """
        # 1. Check spec.yml for per-container override
        per_container = self.spec.get_container_resources_for(container_name)
        if per_container:
            return per_container

        # 2. Check compose service_info for deploy.resources
        deploy_block = service_info.get("deploy", {})
        compose_resources = deploy_block.get("resources", {}) if deploy_block else {}
        if compose_resources:
            return Resources(compose_resources)

        # 3. Fall back to spec.yml global (already resolved with DEFAULT fallback)
        return global_resources

    def _build_containers(
        self,
        parsed_yaml_map: Any,
        image_pull_policy: Optional[str] = None,
    ) -> tuple:
        """Build k8s container specs from parsed compose YAML.

        Returns a tuple of (containers, init_containers, services, volumes)
        where:
        - containers: list of V1Container objects
        - init_containers: list of V1Container objects for init containers
          (compose services with label ``laconic.init-container: "true"``)
        - services: the last services dict processed (used for annotations/labels)
        - volumes: list of V1Volume objects
        """
        containers = []
        init_containers = []
        services = {}
        global_resources = self.spec.get_container_resources()
        if not global_resources:
            global_resources = DEFAULT_CONTAINER_RESOURCES
        for pod_name in parsed_yaml_map:
            pod = parsed_yaml_map[pod_name]
            services = pod["services"]
            for service_name in services:
                container_name = service_name
                service_info = services[service_name]
                image = service_info["image"]
                container_ports = []
                if "ports" in service_info:
                    for raw_port in [str(p) for p in service_info["ports"]]:
                        # Parse protocol suffix (e.g., "8001/udp" -> port=8001,
                        # protocol=UDP)
                        protocol = "TCP"
                        port_str = raw_port
                        if "/" in raw_port:
                            port_str, proto = raw_port.rsplit("/", 1)
                            protocol = proto.upper()
                        # Handle host:container port mapping - use container port
                        if ":" in port_str:
                            port_str = port_str.split(":")[-1]
                        port = int(port_str)
                        container_ports.append(
                            client.V1ContainerPort(
                                container_port=port, protocol=protocol
                            )
                        )
                    if opts.o.debug:
                        print(f"image: {image}")
                        print(f"service ports: {container_ports}")
                merged_envs = (
                    merge_envs(
                        envs_from_compose_file(
                            service_info["environment"], self.environment_variables.map
                        ),
                        self.environment_variables.map,
                    )
                    if "environment" in service_info
                    else self.environment_variables.map
                )
                # Translate docker-compose service names to localhost for sidecars
                # All services in the same pod share the network namespace
                sibling_services = [s for s in services.keys() if s != service_name]
                merged_envs = translate_sidecar_service_names(
                    merged_envs, sibling_services
                )
                envs = envs_from_environment_variables_map(merged_envs)
                if opts.o.debug:
                    print(f"Merged envs: {envs}")
                # Re-write the image tag for remote deployment
                # Note self.app_name has the same value as deployment_id
                image_to_use = (
                    remote_tag_for_image_unique(
                        image, self.spec.get_image_registry(), self.app_name
                    )
                    if self.spec.get_image_registry() is not None
                    else image
                )
                volume_mounts = volume_mounts_for_service(parsed_yaml_map, service_name)
                # Handle command/entrypoint from compose file
                # In docker-compose: entrypoint -> k8s command, command -> k8s args
                container_command = None
                container_args = None
                if "entrypoint" in service_info:
                    entrypoint = service_info["entrypoint"]
                    container_command = (
                        entrypoint if isinstance(entrypoint, list) else [entrypoint]
                    )
                if "command" in service_info:
                    cmd = service_info["command"]
                    container_args = cmd if isinstance(cmd, list) else cmd.split()
                # Add env_from to pull secrets from K8s Secret
                secret_name = f"{self.app_name}-generated-secrets"
                env_from = [
                    client.V1EnvFromSource(
                        secret_ref=client.V1SecretEnvSource(
                            name=secret_name,
                            optional=True,  # Don't fail if no secrets
                        )
                    )
                ]
                # Mount user-declared secrets from spec.yml
                for user_secret_name in self.spec.get_secrets():
                    env_from.append(
                        client.V1EnvFromSource(
                            secret_ref=client.V1SecretEnvSource(
                                name=user_secret_name,
                                optional=True,
                            )
                        )
                    )
                container_resources = self._resolve_container_resources(
                    container_name, service_info, global_resources
                )
                container = client.V1Container(
                    name=container_name,
                    image=image_to_use,
                    image_pull_policy=image_pull_policy,
                    command=container_command,
                    args=container_args,
                    env=envs,
                    env_from=env_from,
                    ports=container_ports if container_ports else None,
                    volume_mounts=volume_mounts,
                    security_context=client.V1SecurityContext(
                        privileged=self.spec.get_privileged(),
                        run_as_user=int(service_info["user"])
                        if "user" in service_info
                        else None,
                        capabilities=client.V1Capabilities(
                            add=self.spec.get_capabilities()
                        )
                        if self.spec.get_capabilities()
                        else None,
                    ),
                    resources=to_k8s_resource_requirements(container_resources),
                )
                # Services with laconic.init-container label become
                # k8s init containers instead of regular containers.
                svc_labels = service_info.get("labels", {})
                if isinstance(svc_labels, list):
                    # docker-compose labels can be a list of "key=value"
                    svc_labels = dict(item.split("=", 1) for item in svc_labels)
                is_init = str(svc_labels.get("laconic.init-container", "")).lower() in (
                    "true",
                    "1",
                    "yes",
                )
                if is_init:
                    init_containers.append(container)
                else:
                    containers.append(container)
        volumes = volumes_for_pod_files(parsed_yaml_map, self.spec, self.app_name)
        return containers, init_containers, services, volumes

    # TODO: put things like image pull policy into an object-scope struct
    def get_deployment(self, image_pull_policy: Optional[str] = None):
        containers, init_containers, services, volumes = self._build_containers(
            self.parsed_pod_yaml_map, image_pull_policy
        )
        registry_config = self.spec.get_image_registry_config()
        if registry_config:
            secret_name = f"{self.app_name}-registry"
            image_pull_secrets = [client.V1LocalObjectReference(name=secret_name)]
        else:
            image_pull_secrets = []

        annotations = None
        labels = {"app": self.app_name}
        if self.stack_name:
            labels["app.kubernetes.io/stack"] = self.stack_name
        affinity = None
        tolerations = None

        if self.spec.get_annotations():
            annotations = {}
            for key, value in self.spec.get_annotations().items():
                for service_name in services:
                    annotations[key.replace("{name}", service_name)] = value

        if self.spec.get_labels():
            for key, value in self.spec.get_labels().items():
                for service_name in services:
                    labels[key.replace("{name}", service_name)] = value

        if self.spec.get_node_affinities():
            affinities = []
            for rule in self.spec.get_node_affinities():
                # TODO add some input validation here
                label_name = rule["label"]
                label_value = rule["value"]
                affinities.append(
                    client.V1NodeSelectorTerm(
                        match_expressions=[
                            client.V1NodeSelectorRequirement(
                                key=label_name, operator="In", values=[label_value]
                            )
                        ]
                    )
                )
            affinity = client.V1Affinity(
                node_affinity=client.V1NodeAffinity(
                    required_during_scheduling_ignored_during_execution=(
                        client.V1NodeSelector(node_selector_terms=affinities)
                    )
                )
            )

        if self.spec.get_node_tolerations():
            tolerations = []
            for toleration in self.spec.get_node_tolerations():
                # TODO add some input validation here
                toleration_key = toleration["key"]
                toleration_value = toleration["value"]
                tolerations.append(
                    client.V1Toleration(
                        effect="NoSchedule",
                        key=toleration_key,
                        operator="Equal",
                        value=toleration_value,
                    )
                )

        use_host_network = self._any_service_has_host_network()
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(annotations=annotations, labels=labels),
            spec=client.V1PodSpec(
                containers=containers,
                init_containers=init_containers or None,
                image_pull_secrets=image_pull_secrets,
                volumes=volumes,
                affinity=affinity,
                tolerations=tolerations,
                runtime_class_name=self.spec.get_runtime_class(),
                host_network=use_host_network or None,
                dns_policy=("ClusterFirstWithHostNet" if use_host_network else None),
            ),
        )
        spec = client.V1DeploymentSpec(
            replicas=self.spec.get_replicas(),
            template=template,
            selector={"matchLabels": {"app": self.app_name}},
        )

        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=f"{self.app_name}-deployment",
                labels={
                    "app": self.app_name,
                    **(
                        {"app.kubernetes.io/stack": self.stack_name}
                        if self.stack_name
                        else {}
                    ),
                },
            ),
            spec=spec,
        )
        return deployment

    def get_jobs(self, image_pull_policy: Optional[str] = None) -> List[client.V1Job]:
        """Build k8s Job objects from parsed job compose files.

        Each job compose file produces a V1Job with:
        - restartPolicy: Never
        - backoffLimit: 0
        - Name: {app_name}-job-{job_name}
        """
        if not self.parsed_job_yaml_map:
            return []

        jobs = []
        registry_config = self.spec.get_image_registry_config()
        if registry_config:
            secret_name = f"{self.app_name}-registry"
            image_pull_secrets = [client.V1LocalObjectReference(name=secret_name)]
        else:
            image_pull_secrets = []

        for job_file in self.parsed_job_yaml_map:
            # Build containers for this single job file
            single_job_map = {job_file: self.parsed_job_yaml_map[job_file]}
            containers, init_containers, _services, volumes = self._build_containers(
                single_job_map, image_pull_policy
            )

            # Derive job name from file path: docker-compose-<name>.yml -> <name>
            base = os.path.basename(job_file)
            # Strip docker-compose- prefix and .yml suffix
            job_name = base
            if job_name.startswith("docker-compose-"):
                job_name = job_name[len("docker-compose-") :]
            if job_name.endswith(".yml"):
                job_name = job_name[: -len(".yml")]
            elif job_name.endswith(".yaml"):
                job_name = job_name[: -len(".yaml")]

            # Use a distinct app label for job pods so they don't get
            # picked up by pods_in_deployment() which queries app={app_name}.
            pod_labels = {
                "app": f"{self.app_name}-job",
                **(
                    {"app.kubernetes.io/stack": self.stack_name}
                    if self.stack_name
                    else {}
                ),
            }
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=pod_labels),
                spec=client.V1PodSpec(
                    containers=containers,
                    init_containers=init_containers or None,
                    image_pull_secrets=image_pull_secrets,
                    volumes=volumes,
                    restart_policy="Never",
                ),
            )
            job_spec = client.V1JobSpec(
                template=template,
                backoff_limit=0,
            )
            job_labels = {
                "app": self.app_name,
                **(
                    {"app.kubernetes.io/stack": self.stack_name}
                    if self.stack_name
                    else {}
                ),
            }
            job = client.V1Job(
                api_version="batch/v1",
                kind="Job",
                metadata=client.V1ObjectMeta(
                    name=f"{self.app_name}-job-{job_name}",
                    labels=job_labels,
                ),
                spec=job_spec,
            )
            jobs.append(job)

        return jobs
