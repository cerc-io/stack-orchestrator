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
import subprocess
from typing import Set

from app.opts import opts


def _run_command(command: str):
    if opts.o.debug:
        print(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    if opts.o.debug:
        print(f"Result: {result}")


def create_cluster(name: str):
    _run_command(f"kind create cluster --name {name}")


def destroy_cluster(name: str):
    _run_command(f"kind delete cluster --name {name}")


def load_images_into_kind(kind_cluster_name: str, image_set: Set[str]):
    for image in image_set:
        _run_command(f"kind load docker-image {image} --name {kind_cluster_name}")


def pods_in_deployment(core_api: client.CoreV1Api, deployment_name: str):
    pods = []
    pod_response = core_api.list_namespaced_pod(namespace="default", label_selector="app=test-app")
    if opts.o.debug:
        print(f"pod_response: {pod_response}")
    for pod_info in pod_response.items:
        pod_name = pod_info.metadata.name
        pods.append(pod_name)
    return pods


def log_stream_from_string(s: str):
    # Note response has to be UTF-8 encoded because the caller expects to decode it
    yield ("ignore", s.encode())


def named_volumes_from_pod_files(parsed_pod_files):
    # Parse the compose files looking for named volumes
    named_volumes = []
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
        if "volumes" in parsed_pod_file:
            volumes = parsed_pod_file["volumes"]
            for volume in volumes.keys():
                # Volume definition looks like:
                # 'laconicd-data': None
                named_volumes.append(volume)
    return named_volumes


def volume_mounts_for_service(parsed_pod_files, service):
    result = []
    # Find the service
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
        if "services" in parsed_pod_file:
            services = parsed_pod_file["services"]
            for service_name in services:
                if service_name == service:
                    service_obj = services[service_name]
                    if "volumes" in service_obj:
                        volumes = service_obj["volumes"]
                        for mount_string in volumes:
                            # Looks like: test-data:/data
                            (volume_name, mount_path) = mount_string.split(":")
                            volume_device = client.V1VolumeMount(mount_path=mount_path, name=volume_name)
                            result.append(volume_device)
    return result


def volumes_for_pod_files(parsed_pod_files):
    result = []
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
        if "volumes" in parsed_pod_file:
            volumes = parsed_pod_file["volumes"]
            for volume_name in volumes.keys():
                claim = client.V1PersistentVolumeClaimVolumeSource(claim_name=volume_name)
                volume = client.V1Volume(name=volume_name, persistent_volume_claim=claim)
                result.append(volume)
    return result
