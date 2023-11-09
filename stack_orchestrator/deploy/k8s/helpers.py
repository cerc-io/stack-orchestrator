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
from dotenv import dotenv_values
import os
from pathlib import Path
import subprocess
from typing import Any, Set, Mapping, List

from stack_orchestrator.opts import opts
from stack_orchestrator.util import get_yaml


def _run_command(command: str):
    if opts.o.debug:
        print(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    if opts.o.debug:
        print(f"Result: {result}")


def create_cluster(name: str, config_file: str):
    _run_command(f"kind create cluster --name {name} --config {config_file}")


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


def get_node_pv_mount_path(volume_name: str):
    return f"/mnt/{volume_name}"


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


def _get_host_paths_for_volumes(parsed_pod_files):
    result = {}
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
        if "volumes" in parsed_pod_file:
            volumes = parsed_pod_file["volumes"]
            for volume_name in volumes.keys():
                volume_definition = volumes[volume_name]
                host_path = volume_definition["driver_opts"]["device"]
                result[volume_name] = host_path
    return result


def _make_absolute_host_path(data_mount_path: Path, deployment_dir: Path) -> Path:
    if os.path.isabs(data_mount_path):
        return data_mount_path
    else:
        # Python Path voodo that looks pretty odd:
        return Path.cwd().joinpath(deployment_dir.joinpath("compose").joinpath(data_mount_path)).resolve()


def parsed_pod_files_map_from_file_names(pod_files):
    parsed_pod_yaml_map : Any = {}
    for pod_file in pod_files:
        with open(pod_file, "r") as pod_file_descriptor:
            parsed_pod_file = get_yaml().load(pod_file_descriptor)
            parsed_pod_yaml_map[pod_file] = parsed_pod_file
    if opts.o.debug:
        print(f"parsed_pod_yaml_map: {parsed_pod_yaml_map}")
    return parsed_pod_yaml_map


def _generate_kind_mounts(parsed_pod_files, deployment_dir):
    volume_definitions = []
    volume_host_path_map = _get_host_paths_for_volumes(parsed_pod_files)
    # Note these paths are relative to the location of the pod files (at present)
    # So we need to fix up to make them correct and absolute because kind assumes
    # relative to the cwd.
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
        if "services" in parsed_pod_file:
            services = parsed_pod_file["services"]
            for service_name in services:
                service_obj = services[service_name]
                if "volumes" in service_obj:
                    volumes = service_obj["volumes"]
                    for mount_string in volumes:
                        # Looks like: test-data:/data
                        (volume_name, mount_path) = mount_string.split(":")
                        volume_definitions.append(
                            f"  - hostPath: {_make_absolute_host_path(volume_host_path_map[volume_name], deployment_dir)}\n"
                            f"    containerPath: {get_node_pv_mount_path(volume_name)}"
                            )
    return (
        "" if len(volume_definitions) == 0 else (
            "  extraMounts:\n"
            f"{''.join(volume_definitions)}"
        )
    )


def _generate_kind_port_mappings(parsed_pod_files):
    port_definitions = []
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
        if "services" in parsed_pod_file:
            services = parsed_pod_file["services"]
            for service_name in services:
                service_obj = services[service_name]
                if "ports" in service_obj:
                    ports = service_obj["ports"]
                    for port_string in ports:
                        # TODO handle the complex cases
                        # Looks like: 80 or something more complicated
                        port_definitions.append(f"  - containerPort: {port_string}\n    hostPort: {port_string}")
    return (
        "" if len(port_definitions) == 0 else (
            "  extraPortMappings:\n"
            f"{''.join(port_definitions)}"
        )
    )


def envs_from_environment_variables_map(map: Mapping[str, str]) -> List[client.V1EnvVar]:
    result = []
    for env_var, env_val in map.items():
        result.append(client.V1EnvVar(env_var, env_val))
    return result


# This needs to know:
# The service ports for the cluster
# The bind mounted volumes for the cluster
#
# Make ports like this:
#  extraPortMappings:
#  - containerPort: 80
#    hostPort: 80
#    # optional: set the bind address on the host
#    # 0.0.0.0 is the current default
#    listenAddress: "127.0.0.1"
#    # optional: set the protocol to one of TCP, UDP, SCTP.
#    # TCP is the default
#    protocol: TCP
# Make bind mounts like this:
#  extraMounts:
#  - hostPath: /path/to/my/files
#    containerPath: /files
def generate_kind_config(deployment_dir: Path):
    compose_file_dir = deployment_dir.joinpath("compose")
    # TODO: this should come from the stack file, not this way
    pod_files = [p for p in compose_file_dir.iterdir() if p.is_file()]
    parsed_pod_files_map = parsed_pod_files_map_from_file_names(pod_files)
    port_mappings_yml = _generate_kind_port_mappings(parsed_pod_files_map)
    mounts_yml = _generate_kind_mounts(parsed_pod_files_map, deployment_dir)
    return (
        "kind: Cluster\n"
        "apiVersion: kind.x-k8s.io/v1alpha4\n"
        "nodes:\n"
        "- role: control-plane\n"
        f"{port_mappings_yml}\n"
        f"{mounts_yml}\n"
    )


def env_var_map_from_file(file: Path) -> Mapping[str, str]:
    return dotenv_values(file)
