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

from kubernetes import client
from typing import Any, List, Set

from stack_orchestrator.opts import opts
from stack_orchestrator.deploy.k8s.helpers import named_volumes_from_pod_files, volume_mounts_for_service, volumes_for_pod_files
from stack_orchestrator.deploy.k8s.helpers import get_node_pv_mount_path
from stack_orchestrator.deploy.k8s.helpers import env_var_map_from_file, envs_from_environment_variables_map
from stack_orchestrator.deploy.deploy_util import parsed_pod_files_map_from_file_names, images_for_deployment
from stack_orchestrator.deploy.deploy_types import DeployEnvVars
from stack_orchestrator.deploy.spec import Spec
from stack_orchestrator.deploy.images import remote_tag_for_image


class ClusterInfo:
    parsed_pod_yaml_map: Any
    image_set: Set[str] = set()
    app_name: str = "test-app"
    deployment_name: str = "test-deployment"
    environment_variables: DeployEnvVars
    spec: Spec

    def __init__(self) -> None:
        pass

    def int(self, pod_files: List[str], compose_env_file, spec: Spec):
        self.parsed_pod_yaml_map = parsed_pod_files_map_from_file_names(pod_files)
        # Find the set of images in the pods
        self.image_set = images_for_deployment(pod_files)
        self.environment_variables = DeployEnvVars(env_var_map_from_file(compose_env_file))
        self.spec = spec
        if (opts.o.debug):
            print(f"Env vars: {self.environment_variables.map}")

    def get_ingress(self):
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
            )]
            paths = []
            for route in http_proxy_info["routes"]:
                path = route["path"]
                proxy_to = route["proxy-to"]
                if opts.o.debug:
                    print(f"proxy config: {path} -> {proxy_to}")
                paths.append(client.V1HTTPIngressPath(
                    path_type="Prefix",
                    path=path,
                    backend=client.V1IngressBackend(
                        service=client.V1IngressServiceBackend(
                            # TODO: this looks wrong
                            name=self.deployment_name,
                            # TODO: pull port number from the service
                            port=client.V1ServiceBackendPort(number=80)
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

    def get_service(self):
        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=f"{self.app_name}-service"),
            spec=client.V1ServiceSpec(
                type="ClusterIP",
                ports=[client.V1ServicePort(
                    port=80,
                    target_port=80
                )],
                selector={"matchLabels":
                          {"app": self.app_name}}
            )
        )
        return service

    def get_pvcs(self):
        result = []
        volumes = named_volumes_from_pod_files(self.parsed_pod_yaml_map)
        if opts.o.debug:
            print(f"Volumes: {volumes}")
        for volume_name in volumes:
            spec = client.V1PersistentVolumeClaimSpec(
                access_modes=["ReadWriteOnce"],
                storage_class_name="manual",
                resources=client.V1ResourceRequirements(
                    requests={"storage": "2Gi"}
                ),
                volume_name=volume_name
            )
            pvc = client.V1PersistentVolumeClaim(
                metadata=client.V1ObjectMeta(name=volume_name,
                                             labels={"volume-label": volume_name}),
                spec=spec,
            )
            result.append(pvc)
        return result

    def get_pvs(self):
        result = []
        volumes = named_volumes_from_pod_files(self.parsed_pod_yaml_map)
        for volume_name in volumes:
            spec = client.V1PersistentVolumeSpec(
                storage_class_name="manual",
                access_modes=["ReadWriteOnce"],
                capacity={"storage": "2Gi"},
                host_path=client.V1HostPathVolumeSource(path=get_node_pv_mount_path(volume_name))
            )
            pv = client.V1PersistentVolume(
                metadata=client.V1ObjectMeta(name=volume_name,
                                             labels={"volume-label": volume_name}),
                spec=spec,
            )
            result.append(pv)
        return result

    # to suit the deployment, and also annotate the container specs to point at said volumes
    def get_deployment(self):
        containers = []
        for pod_name in self.parsed_pod_yaml_map:
            pod = self.parsed_pod_yaml_map[pod_name]
            services = pod["services"]
            for service_name in services:
                container_name = service_name
                service_info = services[service_name]
                image = service_info["image"]
                # Re-write the image tag for remote deployment
                image_to_use = remote_tag_for_image(
                    image, self.spec.get_image_registry()) if self.spec.get_image_registry() is not None else image
                volume_mounts = volume_mounts_for_service(self.parsed_pod_yaml_map, service_name)
                container = client.V1Container(
                    name=container_name,
                    image=image_to_use,
                    env=envs_from_environment_variables_map(self.environment_variables.map),
                    ports=[client.V1ContainerPort(container_port=80)],
                    volume_mounts=volume_mounts,
                    resources=client.V1ResourceRequirements(
                        requests={"cpu": "100m", "memory": "200Mi"},
                        limits={"cpu": "500m", "memory": "500Mi"},
                    ),
                )
                containers.append(container)
        volumes = volumes_for_pod_files(self.parsed_pod_yaml_map)
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": self.app_name}),
            spec=client.V1PodSpec(containers=containers, volumes=volumes),
        )
        spec = client.V1DeploymentSpec(
            replicas=1, template=template, selector={
                "matchLabels":
                {"app": self.app_name}})

        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=self.deployment_name),
            spec=spec,
        )
        return deployment
