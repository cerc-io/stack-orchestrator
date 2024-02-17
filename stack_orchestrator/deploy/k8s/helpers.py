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

from kubernetes import client, utils, watch
import os
from pathlib import Path
import subprocess
import re
from typing import Set, Mapping, List

from stack_orchestrator.util import get_k8s_dir, error_exit
from stack_orchestrator.opts import opts
from stack_orchestrator.deploy.deploy_util import parsed_pod_files_map_from_file_names
from stack_orchestrator.deploy.deployer import DeployerException


def _run_command(command: str):
    if opts.o.debug:
        print(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    if opts.o.debug:
        print(f"Result: {result}")
    return result


def create_cluster(name: str, config_file: str):
    result = _run_command(f"kind create cluster --name {name} --config {config_file}")
    if result.returncode != 0:
        raise DeployerException(f"kind create cluster failed: {result}")


def destroy_cluster(name: str):
    _run_command(f"kind delete cluster --name {name}")


def wait_for_ingress_in_kind():
    core_v1 = client.CoreV1Api()
    for i in range(20):
        warned_waiting = False
        w = watch.Watch()
        for event in w.stream(func=core_v1.list_namespaced_pod,
                              namespace="ingress-nginx",
                              label_selector="app.kubernetes.io/component=controller",
                              timeout_seconds=30):
            if event['object'].status.container_statuses:
                if event['object'].status.container_statuses[0].ready is True:
                    if warned_waiting:
                        print("Ingress controller is ready")
                    return
            print("Waiting for ingress controller to become ready...")
            warned_waiting = True
    error_exit("ERROR: Timed out waiting for ingress to become ready")


def install_ingress_for_kind():
    api_client = client.ApiClient()
    ingress_install = os.path.abspath(get_k8s_dir().joinpath("components", "ingress", "ingress-nginx-kind-deploy.yaml"))
    if opts.o.debug:
        print("Installing nginx ingress controller in kind cluster")
    utils.create_from_yaml(api_client, yaml_file=ingress_install)


def load_images_into_kind(kind_cluster_name: str, image_set: Set[str]):
    for image in image_set:
        result = _run_command(f"kind load docker-image {image} --name {kind_cluster_name}")
        if result.returncode != 0:
            raise DeployerException(f"kind create cluster failed: {result}")


def pods_in_deployment(core_api: client.CoreV1Api, deployment_name: str):
    pods = []
    pod_response = core_api.list_namespaced_pod(namespace="default", label_selector=f"app={deployment_name}")
    if opts.o.debug:
        print(f"pod_response: {pod_response}")
    for pod_info in pod_response.items:
        pod_name = pod_info.metadata.name
        pods.append(pod_name)
    return pods


def containers_in_pod(core_api: client.CoreV1Api, pod_name: str):
    containers = []
    pod_response = core_api.read_namespaced_pod(pod_name, namespace="default")
    if opts.o.debug:
        print(f"pod_response: {pod_response}")
    pod_containers = pod_response.spec.containers
    for pod_container in pod_containers:
        containers.append(pod_container.name)
    return containers


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
            for volume, value in volumes.items():
                # Volume definition looks like:
                # 'laconicd-data': None
                named_volumes.append(volume)
    return named_volumes


def get_kind_pv_bind_mount_path(volume_name: str):
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
                            # Looks like: test-data:/data or test-data:/data:ro or test-data:/data:rw
                            if opts.o.debug:
                                print(f"mount_string: {mount_string}")
                            mount_split = mount_string.split(":")
                            volume_name = mount_split[0]
                            mount_path = mount_split[1]
                            mount_options = mount_split[2] if len(mount_split) == 3 else None
                            if opts.o.debug:
                                print(f"volume_name: {volume_name}")
                                print(f"mount path: {mount_path}")
                                print(f"mount options: {mount_options}")
                            volume_device = client.V1VolumeMount(
                                mount_path=mount_path,
                                name=volume_name,
                                read_only="ro" == mount_options
                            )
                            result.append(volume_device)
    return result


def volumes_for_pod_files(parsed_pod_files, spec, app_name):
    result = []
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
        if "volumes" in parsed_pod_file:
            volumes = parsed_pod_file["volumes"]
            for volume_name in volumes.keys():
                if volume_name in spec.get_configmaps():
                    config_map = client.V1ConfigMapVolumeSource(name=f"{app_name}-{volume_name}")
                    volume = client.V1Volume(name=volume_name, config_map=config_map)
                    result.append(volume)
                else:
                    claim = client.V1PersistentVolumeClaimVolumeSource(claim_name=f"{app_name}-{volume_name}")
                    volume = client.V1Volume(name=volume_name, persistent_volume_claim=claim)
                    result.append(volume)
    return result


def _get_host_paths_for_volumes(deployment_context):
    return deployment_context.spec.get_volumes()


def _make_absolute_host_path(data_mount_path: Path, deployment_dir: Path) -> Path:
    if os.path.isabs(data_mount_path):
        return data_mount_path
    else:
        # Python Path voodo that looks pretty odd:
        return Path.cwd().joinpath(deployment_dir.joinpath(data_mount_path)).resolve()


def _generate_kind_mounts(parsed_pod_files, deployment_dir, deployment_context):
    volume_definitions = []
    volume_host_path_map = _get_host_paths_for_volumes(deployment_context)
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
                        # Looks like: test-data:/data or test-data:/data:ro or test-data:/data:rw
                        if opts.o.debug:
                            print(f"mount_string: {mount_string}")
                        mount_split = mount_string.split(":")
                        volume_name = mount_split[0]
                        mount_path = mount_split[1]
                        if opts.o.debug:
                            print(f"volume_name: {volume_name}")
                            print(f"map: {volume_host_path_map}")
                            print(f"mount path: {mount_path}")
                        if volume_name not in deployment_context.spec.get_configmaps():
                            if volume_host_path_map[volume_name]:
                                volume_definitions.append(
                                    f"  - hostPath: {_make_absolute_host_path(volume_host_path_map[volume_name], deployment_dir)}\n"
                                    f"    containerPath: {get_kind_pv_bind_mount_path(volume_name)}\n"
                                )
    return (
        "" if len(volume_definitions) == 0 else (
            "  extraMounts:\n"
            f"{''.join(volume_definitions)}"
        )
    )


# TODO: decide if we need this functionality
def _generate_kind_port_mappings_from_services(parsed_pod_files):
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
                        port_definitions.append(f"  - containerPort: {port_string}\n    hostPort: {port_string}\n")
    return (
        "" if len(port_definitions) == 0 else (
            "  extraPortMappings:\n"
            f"{''.join(port_definitions)}"
        )
    )


def _generate_kind_port_mappings(parsed_pod_files):
    port_definitions = []
    # For now we just map port 80 for the nginx ingress controller we install in kind
    port_string = "80"
    port_definitions.append(f"  - containerPort: {port_string}\n    hostPort: {port_string}\n")
    return (
        "" if len(port_definitions) == 0 else (
            "  extraPortMappings:\n"
            f"{''.join(port_definitions)}"
        )
    )


# Note: this makes any duplicate definition in b overwrite a
def merge_envs(a: Mapping[str, str], b: Mapping[str, str]) -> Mapping[str, str]:
    result = {**a, **b}
    return result


def _expand_shell_vars(raw_val: str) -> str:
    # could be: <string> or ${<env-var-name>} or ${<env-var-name>:-<default-value>}
    # TODO: implement support for variable substitution and default values
    # if raw_val is like ${<something>} print a warning and substitute an empty string
    # otherwise return raw_val
    match = re.search(r"^\$\{(.*)\}$", raw_val)
    if match:
        print(f"WARNING: found unimplemented environment variable substitution: {raw_val}")
    else:
        return raw_val


# TODO: handle the case where the same env var is defined in multiple places
def envs_from_compose_file(compose_file_envs: Mapping[str, str]) -> Mapping[str, str]:
    result = {}
    for env_var, env_val in compose_file_envs.items():
        expanded_env_val = _expand_shell_vars(env_val)
        result.update({env_var: expanded_env_val})
    return result


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
def generate_kind_config(deployment_dir: Path, deployment_context):
    compose_file_dir = deployment_dir.joinpath("compose")
    # TODO: this should come from the stack file, not this way
    pod_files = [p for p in compose_file_dir.iterdir() if p.is_file()]
    parsed_pod_files_map = parsed_pod_files_map_from_file_names(pod_files)
    port_mappings_yml = _generate_kind_port_mappings(parsed_pod_files_map)
    mounts_yml = _generate_kind_mounts(parsed_pod_files_map, deployment_dir, deployment_context)
    return (
        "kind: Cluster\n"
        "apiVersion: kind.x-k8s.io/v1alpha4\n"
        "nodes:\n"
        "- role: control-plane\n"
        "  kubeadmConfigPatches:\n"
        "    - |\n"
        "      kind: InitConfiguration\n"
        "      nodeRegistration:\n"
        "        kubeletExtraArgs:\n"
        "          node-labels: \"ingress-ready=true\"\n"
        f"{port_mappings_yml}\n"
        f"{mounts_yml}\n"
    )
