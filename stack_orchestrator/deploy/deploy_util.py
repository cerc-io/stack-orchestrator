# Copyright © 2022, 2023 Vulcanize

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

from typing import List, Any
from stack_orchestrator.deploy.deploy_types import DeployCommandContext, VolumeMapping
from stack_orchestrator.util import (
    get_parsed_stack_config,
    get_yaml,
    get_pod_list,
    resolve_compose_file,
)
from stack_orchestrator.opts import opts


def _container_image_from_service(stack: str, service: str):
    # Parse the compose files looking for the image name of the specified service
    image_name = None
    parsed_stack = get_parsed_stack_config(stack)
    pods = get_pod_list(parsed_stack)
    yaml = get_yaml()
    for pod in pods:
        pod_file_path = resolve_compose_file(stack, pod)
        parsed_pod_file = yaml.load(open(pod_file_path, "r"))
        if "services" in parsed_pod_file:
            services = parsed_pod_file["services"]
            if service in services:
                service_definition = services[service]
                if "image" in service_definition:
                    image_name = service_definition["image"]
    return image_name


def parsed_pod_files_map_from_file_names(pod_files):
    parsed_pod_yaml_map: Any = {}
    for pod_file in pod_files:
        with open(pod_file, "r") as pod_file_descriptor:
            parsed_pod_file = get_yaml().load(pod_file_descriptor)
            parsed_pod_yaml_map[pod_file] = parsed_pod_file
    if opts.o.debug:
        print(f"parsed_pod_yaml_map: {parsed_pod_yaml_map}")
    return parsed_pod_yaml_map


def images_for_deployment(pod_files: List[str]):
    image_set = set()
    parsed_pod_yaml_map = parsed_pod_files_map_from_file_names(pod_files)
    # Find the set of images in the pods
    for pod_name in parsed_pod_yaml_map:
        pod = parsed_pod_yaml_map[pod_name]
        services = pod["services"]
        for service_name in services:
            service_info = services[service_name]
            image = service_info["image"]
            image_set.add(image)
    if opts.o.debug:
        print(f"image_set: {image_set}")
    return image_set


def _volumes_to_docker(mounts: List[VolumeMapping]):
    # Example from doc: [("/", "/host"), ("/etc/hosts", "/etc/hosts", "rw")]
    result = []
    for mount in mounts:
        docker_volume = (mount.host_path, mount.container_path)
        result.append(docker_volume)
    return result


def run_container_command(
    ctx: DeployCommandContext, service: str, command: str, mounts: List[VolumeMapping]
):
    deployer = ctx.deployer
    if deployer is None:
        raise ValueError("Deployer is not configured")
    container_image = _container_image_from_service(ctx.stack, service)
    if container_image is None:
        raise ValueError(f"Container image not found for service: {service}")
    docker_volumes = _volumes_to_docker(mounts)
    if ctx.cluster_context.options.debug:
        print(f"Running this command in {service} container: {command}")
    docker_output = deployer.run(
        container_image,
        ["-c", command],
        entrypoint="sh",
        # Current laconicd container has a bug where it crashes when run not
        # as root
        # Commented out line below is a workaround. Created files end up
        # owned by root on the host
        # user=f"{os.getuid()}:{os.getgid()}",
        volumes=docker_volumes,
    )
    # There doesn't seem to be a way to get an exit code from docker.run()
    return (docker_output, 0)
