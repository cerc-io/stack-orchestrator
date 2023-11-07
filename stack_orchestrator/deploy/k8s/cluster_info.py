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
from stack_orchestrator.deploy.k8s.helpers import parsed_pod_files_map_from_file_names


class ClusterInfo:
    parsed_pod_yaml_map: Any = {}
    image_set: Set[str] = set()
    app_name: str = "test-app"
    deployment_name: str = "test-deployment"

    def __init__(self) -> None:
        pass

    def int_from_pod_files(self, pod_files: List[str]):
        self.parsed_pod_yaml_map = parsed_pod_files_map_from_file_names(pod_files)
        # Find the set of images in the pods
        for pod_name in self.parsed_pod_yaml_map:
            pod = self.parsed_pod_yaml_map[pod_name]
            services = pod["services"]
            for service_name in services:
                service_info = services[service_name]
                image = service_info["image"]
                self.image_set.add(image)
        if opts.o.debug:
            print(f"image_set: {self.image_set}")

    def get_pvcs(self):
        result = []
        volumes = named_volumes_from_pod_files(self.parsed_pod_yaml_map)
        if opts.o.debug:
            print(f"Volumes: {volumes}")
        for volume_name in volumes:
            spec = client.V1PersistentVolumeClaimSpec(
                storage_class_name="standard",
                access_modes=["ReadWriteOnce"],
                resources=client.V1ResourceRequirements(
                    requests={"storage": "2Gi"}
                )
            )
            pvc = client.V1PersistentVolumeClaim(
                metadata=client.V1ObjectMeta(name=volume_name,
                                             labels={"volume-label": volume_name}),
                spec=spec,
            )
            result.append(pvc)
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
                volume_mounts = volume_mounts_for_service(self.parsed_pod_yaml_map, service_name)
                container = client.V1Container(
                    name=container_name,
                    image=image,
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
