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

from kubernetes import client
from typing import Any, List, Set

from stack_orchestrator.opts import opts
from stack_orchestrator.util import env_var_map_from_file
from stack_orchestrator.deploy.k8s.helpers import named_volumes_from_pod_files, volume_mounts_for_service, volumes_for_pod_files
from stack_orchestrator.deploy.k8s.helpers import get_kind_pv_bind_mount_path
from stack_orchestrator.deploy.k8s.helpers import envs_from_environment_variables_map, envs_from_compose_file, merge_envs
from stack_orchestrator.deploy.deploy_util import parsed_pod_files_map_from_file_names, images_for_deployment
from stack_orchestrator.deploy.deploy_types import DeployEnvVars
from stack_orchestrator.deploy.spec import Spec, Resources, ResourceLimits
from stack_orchestrator.deploy.images import remote_tag_for_image

DEFAULT_VOLUME_RESOURCES = Resources({
    "reservations": {"storage": "2Gi"}
})

DEFAULT_CONTAINER_RESOURCES = Resources({
    "reservations": {"cpus": "0.1", "memory": "200M"},
    "limits": {"cpus": "1.0", "memory": "2000M"},
})


def to_k8s_resource_requirements(resources: Resources) -> client.V1ResourceRequirements:
    def to_dict(limits: ResourceLimits):
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
        requests=to_dict(resources.reservations),
        limits=to_dict(resources.limits)
    )


class ClusterInfo:
    parsed_pod_yaml_map: Any
    image_set: Set[str] = set()
    app_name: str
    environment_variables: DeployEnvVars
    spec: Spec

    def __init__(self) -> None:
        pass

    def int(self, pod_files: List[str], compose_env_file, deployment_name, spec: Spec):
        self.parsed_pod_yaml_map = parsed_pod_files_map_from_file_names(pod_files)
        # Find the set of images in the pods
        self.image_set = images_for_deployment(pod_files)
        self.environment_variables = DeployEnvVars(env_var_map_from_file(compose_env_file))
        self.app_name = deployment_name
        self.spec = spec
        if (opts.o.debug):
            print(f"Env vars: {self.environment_variables.map}")

    def get_nodeport(self):
        for pod_name in self.parsed_pod_yaml_map:
            pod = self.parsed_pod_yaml_map[pod_name]
            services = pod["services"]
            for service_name in services:
                service_info = services[service_name]
                if "ports" in service_info:
                    port = int(service_info["ports"][0])
                    if opts.o.debug:
                        print(f"service port: {port}")
        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=f"{self.app_name}-nodeport"),
            spec=client.V1ServiceSpec(
                type="NodePort",
                ports=[client.V1ServicePort(
                    port=port,
                    target_port=port
                )],
                selector={"app": self.app_name}
            )
        )
        return service

    def get_ingress(self, use_tls=False):
        # No ingress for a deployment that has no http-proxy defined, for now
        http_proxy_info_list = self.spec.get_http_proxy()
        ingress = None
        if http_proxy_info_list:
            # TODO: handle multiple definitions
            http_proxy_info = http_proxy_info_list[0]
            if opts.o.debug:
                print(f"http-proxy: {http_proxy_info}")
            # TODO: good enough parsing for webapp deployment for now
            host_name = http_proxy_info["host-name"]
            rules = []
            tls = [client.V1IngressTLS(
                hosts=[host_name],
                secret_name=f"{self.app_name}-tls"
            )] if use_tls else None
            paths = []
            for route in http_proxy_info["routes"]:
                path = route["path"]
                proxy_to = route["proxy-to"]
                if opts.o.debug:
                    print(f"proxy config: {path} -> {proxy_to}")
                # proxy_to has the form <service>:<port>
                proxy_to_port = int(proxy_to.split(":")[1])
                paths.append(client.V1HTTPIngressPath(
                    path_type="Prefix",
                    path=path,
                    backend=client.V1IngressBackend(
                        service=client.V1IngressServiceBackend(
                            # TODO: this looks wrong
                            name=f"{self.app_name}-service",
                            # TODO: pull port number from the service
                            port=client.V1ServiceBackendPort(number=proxy_to_port)
                        )
                    )
                ))
            rules.append(client.V1IngressRule(
                host=host_name,
                http=client.V1HTTPIngressRuleValue(
                    paths=paths
                )
            ))
            spec = client.V1IngressSpec(
                tls=tls,
                rules=rules
            )
            ingress = client.V1Ingress(
                metadata=client.V1ObjectMeta(
                    name=f"{self.app_name}-ingress",
                    annotations={
                        "kubernetes.io/ingress.class": "nginx",
                        "cert-manager.io/cluster-issuer": "letsencrypt-prod"
                    }
                ),
                spec=spec
            )
        return ingress

    # TODO: suppoprt multiple services
    def get_service(self):
        for pod_name in self.parsed_pod_yaml_map:
            pod = self.parsed_pod_yaml_map[pod_name]
            services = pod["services"]
            for service_name in services:
                service_info = services[service_name]
                if "ports" in service_info:
                    port = int(service_info["ports"][0])
                    if opts.o.debug:
                        print(f"service port: {port}")
        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=f"{self.app_name}-service"),
            spec=client.V1ServiceSpec(
                type="ClusterIP",
                ports=[client.V1ServicePort(
                    port=port,
                    target_port=port
                )],
                selector={"app": self.app_name}
            )
        )
        return service

    def get_pvcs(self):
        result = []
        spec_volumes = self.spec.get_volumes()
        named_volumes = named_volumes_from_pod_files(self.parsed_pod_yaml_map)
        resources = self.spec.get_volume_resources()
        if not resources:
            resources = DEFAULT_VOLUME_RESOURCES
        if opts.o.debug:
            print(f"Spec Volumes: {spec_volumes}")
            print(f"Named Volumes: {named_volumes}")
            print(f"Resources: {resources}")
        for volume_name, volume_path in spec_volumes.items():
            if volume_name not in named_volumes:
                if opts.o.debug:
                    print(f"{volume_name} not in pod files")
                continue

            labels = {
                "app": self.app_name,
                "volume-label": f"{self.app_name}-{volume_name}"
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
                resources=to_k8s_resource_requirements(resources),
                volume_name=k8s_volume_name
            )
            pvc = client.V1PersistentVolumeClaim(
                metadata=client.V1ObjectMeta(name=f"{self.app_name}-{volume_name}", labels=labels),
                spec=spec
            )
            result.append(pvc)
        return result

    def get_configmaps(self):
        result = []
        spec_configmaps = self.spec.get_configmaps()
        named_volumes = named_volumes_from_pod_files(self.parsed_pod_yaml_map)
        for cfg_map_name, cfg_map_path in spec_configmaps.items():
            if cfg_map_name not in named_volumes:
                if opts.o.debug:
                    print(f"{cfg_map_name} not in pod files")
                continue

            if not cfg_map_path.startswith("/"):
                cfg_map_path = os.path.join(os.path.dirname(self.spec.file_path), cfg_map_path)

            # Read in all the files at a single-level of the directory.  This mimics the behavior
            # of `kubectl create configmap foo --from-file=/path/to/dir`
            data = {}
            for f in os.listdir(cfg_map_path):
                full_path = os.path.join(cfg_map_path, f)
                if os.path.isfile(full_path):
                    data[f] = open(full_path, 'rt').read()

            spec = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(name=f"{self.app_name}-{cfg_map_name}",
                                             labels={"configmap-label": cfg_map_name}),
                data=data
            )
            result.append(spec)
        return result

    def get_pvs(self):
        result = []
        spec_volumes = self.spec.get_volumes()
        named_volumes = named_volumes_from_pod_files(self.parsed_pod_yaml_map)
        resources = self.spec.get_volume_resources()
        if not resources:
            resources = DEFAULT_VOLUME_RESOURCES
        for volume_name, volume_path in spec_volumes.items():
            # We only need to create a volume if it is fully qualified HostPath.
            # Otherwise, we create the PVC and expect the node to allocate the volume for us.
            if not volume_path:
                if opts.o.debug:
                    print(f"{volume_name} does not require an explicit PersistentVolume, since it is not a bind-mount.")
                continue

            if volume_name not in named_volumes:
                if opts.o.debug:
                    print(f"{volume_name} not in pod files")
                continue

            if not os.path.isabs(volume_path):
                print(f"WARNING: {volume_name}:{volume_path} is not absolute, cannot bind volume.")
                continue

            if self.spec.is_kind_deployment():
                host_path = client.V1HostPathVolumeSource(path=get_kind_pv_bind_mount_path(volume_name))
            else:
                host_path = client.V1HostPathVolumeSource(path=volume_path)
            spec = client.V1PersistentVolumeSpec(
                storage_class_name="manual",
                access_modes=["ReadWriteOnce"],
                capacity=to_k8s_resource_requirements(resources).requests,
                host_path=host_path
            )
            pv = client.V1PersistentVolume(
                metadata=client.V1ObjectMeta(name=f"{self.app_name}-{volume_name}",
                                             labels={"volume-label": f"{self.app_name}-{volume_name}"}),
                spec=spec,
            )
            result.append(pv)
        return result

    # TODO: put things like image pull policy into an object-scope struct
    def get_deployment(self, image_pull_policy: str = None):
        containers = []
        resources = self.spec.get_container_resources()
        if not resources:
            resources = DEFAULT_CONTAINER_RESOURCES
        for pod_name in self.parsed_pod_yaml_map:
            pod = self.parsed_pod_yaml_map[pod_name]
            services = pod["services"]
            for service_name in services:
                container_name = service_name
                service_info = services[service_name]
                image = service_info["image"]
                if "ports" in service_info:
                    port = int(service_info["ports"][0])
                    if opts.o.debug:
                        print(f"image: {image}")
                        print(f"service port: {port}")
                merged_envs = merge_envs(
                    envs_from_compose_file(
                        service_info["environment"]), self.environment_variables.map
                ) if "environment" in service_info else self.environment_variables.map
                envs = envs_from_environment_variables_map(merged_envs)
                if opts.o.debug:
                    print(f"Merged envs: {envs}")
                # Re-write the image tag for remote deployment
                image_to_use = remote_tag_for_image(
                    image, self.spec.get_image_registry()) if self.spec.get_image_registry() is not None else image
                volume_mounts = volume_mounts_for_service(self.parsed_pod_yaml_map, service_name)
                container = client.V1Container(
                    name=container_name,
                    image=image_to_use,
                    image_pull_policy=image_pull_policy,
                    env=envs,
                    ports=[client.V1ContainerPort(container_port=port)],
                    volume_mounts=volume_mounts,
                    security_context=client.V1SecurityContext(
                        privileged=self.spec.get_privileged(),
                        capabilities=client.V1Capabilities(
                            add=self.spec.get_capabilities()
                        ) if self.spec.get_capabilities() else None
                    ),
                    resources=to_k8s_resource_requirements(resources),
                )
                containers.append(container)
        volumes = volumes_for_pod_files(self.parsed_pod_yaml_map, self.spec, self.app_name)
        image_pull_secrets = [client.V1LocalObjectReference(name="laconic-registry")]

        annotations = None
        labels = {"app": self.app_name}

        if self.spec.get_annotations():
            annotations = {}
            for key, value in self.spec.get_annotations().items():
                for service_name in services:
                    annotations[key.replace("{name}", service_name)] = value

        if self.spec.get_labels():
            for key, value in self.spec.get_labels().items():
                for service_name in services:
                    labels[key.replace("{name}", service_name)] = value

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                annotations=annotations,
                labels=labels
            ),
            spec=client.V1PodSpec(containers=containers, image_pull_secrets=image_pull_secrets, volumes=volumes),
        )
        spec = client.V1DeploymentSpec(
            replicas=1, template=template, selector={
                "matchLabels":
                {"app": self.app_name}})

        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=f"{self.app_name}-deployment"),
            spec=spec,
        )
        return deployment
