# Copyright © 2022, 2023 Cerc

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

import click
from importlib import util
import os
from pathlib import Path
from shutil import copyfile, copytree
import sys
from app.util import get_stack_file_path, get_parsed_deployment_spec, get_parsed_stack_config, global_options, get_yaml, get_compose_file_dir
from app.deploy_types import DeploymentContext, DeployCommandContext


def _make_default_deployment_dir():
    return "deployment-001"


def _get_ports(stack):
    ports = {}
    parsed_stack = get_parsed_stack_config(stack)
    pods = parsed_stack["pods"]
    yaml = get_yaml()
    for pod in pods:
        pod_file_path = os.path.join(get_compose_file_dir(), f"docker-compose-{pod}.yml")
        parsed_pod_file = yaml.load(open(pod_file_path, "r"))
        if "services" in parsed_pod_file:
            for svc_name, svc in parsed_pod_file["services"].items():
                if "ports" in svc:
                    # Ports can appear as strings or numbers.  We normalize them as strings.
                    ports[svc_name] = [ str(x) for x in svc["ports"] ]
    return ports


def _get_named_volumes(stack):
    # Parse the compose files looking for named volumes
    named_volumes = []
    parsed_stack = get_parsed_stack_config(stack)
    pods = parsed_stack["pods"]
    yaml = get_yaml()
    for pod in pods:
        pod_file_path = os.path.join(get_compose_file_dir(), f"docker-compose-{pod}.yml")
        parsed_pod_file = yaml.load(open(pod_file_path, "r"))
        if "volumes" in parsed_pod_file:
            volumes = parsed_pod_file["volumes"]
            for volume in volumes.keys():
                # Volume definition looks like:
                # 'laconicd-data': None
                named_volumes.append(volume)
    return named_volumes


# If we're mounting a volume from a relatie path, then we
# assume the directory doesn't exist yet and create it
# so the deployment will start
# Also warn if the path is absolute and doesn't exist
def _create_bind_dir_if_relative(volume, path_string, compose_dir):
    path = Path(path_string)
    if not path.is_absolute():
        absolute_path = Path(compose_dir).parent.joinpath(path)
        absolute_path.mkdir(parents=True, exist_ok=True)
    else:
        if not path.exists():
            print(f"WARNING: mount path for volume {volume} does not exist: {path_string}")


# See: https://stackoverflow.com/questions/45699189/editing-docker-compose-yml-with-pyyaml
def _fixup_pod_file(pod, spec, compose_dir):
    # Fix up volumes
    if "volumes" in spec:
        spec_volumes = spec["volumes"]
        if "volumes" in pod:
            pod_volumes = pod["volumes"]
            for volume in pod_volumes.keys():
                if volume in spec_volumes:
                    volume_spec = spec_volumes[volume]
                    volume_spec_fixedup = volume_spec if Path(volume_spec).is_absolute() else f".{volume_spec}"
                    _create_bind_dir_if_relative(volume, volume_spec, compose_dir)
                    new_volume_spec = {"driver": "local",
                                       "driver_opts": {
                                          "type": "none",
                                          "device": volume_spec_fixedup,
                                          "o": "bind"
                                       }
                                       }
                    pod["volumes"][volume] = new_volume_spec
    # Fix up ports
    if "ports" in spec:
        spec_ports = spec["ports"]
        for container_name, container_ports in spec_ports.items():
            if container_name in pod["services"]:
                pod["services"][container_name]["ports"] = container_ports


def call_stack_deploy_init(deploy_command_context):
    # Link with the python file in the stack
    # Call a function in it
    # If no function found, return None
    python_file_path = get_stack_file_path(deploy_command_context.stack).parent.joinpath("deploy", "commands.py")
    if python_file_path.exists():
        spec = util.spec_from_file_location("commands", python_file_path)
        imported_stack = util.module_from_spec(spec)
        spec.loader.exec_module(imported_stack)
        return imported_stack.init(deploy_command_context)
    else:
        return None


# TODO: fold this with function above
def call_stack_deploy_setup(deploy_command_context, extra_args):
    # Link with the python file in the stack
    # Call a function in it
    # If no function found, return None
    python_file_path = get_stack_file_path(deploy_command_context.stack).parent.joinpath("deploy", "commands.py")
    if python_file_path.exists():
        spec = util.spec_from_file_location("commands", python_file_path)
        imported_stack = util.module_from_spec(spec)
        spec.loader.exec_module(imported_stack)
        return imported_stack.setup(deploy_command_context, extra_args)
    else:
        return None


# TODO: fold this with function above
def call_stack_deploy_create(deployment_context):
    # Link with the python file in the stack
    # Call a function in it
    # If no function found, return None
    python_file_path = get_stack_file_path(deployment_context.command_context.stack).parent.joinpath("deploy", "commands.py")
    if python_file_path.exists():
        spec = util.spec_from_file_location("commands", python_file_path)
        imported_stack = util.module_from_spec(spec)
        spec.loader.exec_module(imported_stack)
        return imported_stack.create(deployment_context)
    else:
        return None


# Inspect the pod yaml to find config files referenced in subdirectories
# other than the one associated with the pod
def _find_extra_config_dirs(parsed_pod_file, pod):
    config_dirs = set()
    services = parsed_pod_file["services"]
    for service in services:
        service_info = services[service]
        if "volumes" in service_info:
            for volume in service_info["volumes"]:
                if ":" in volume:
                    host_path = volume.split(":")[0]
                    if host_path.startswith("../config"):
                        config_dir = host_path.split("/")[2]
                        if config_dir != pod:
                            config_dirs.add(config_dir)
    return config_dirs


@click.command()
@click.option("--output", required=True, help="Write yaml spec file here")
@click.pass_context
def init(ctx, output):
    yaml = get_yaml()
    stack = global_options(ctx).stack
    verbose = global_options(ctx).verbose
    default_spec_file_content = call_stack_deploy_init(ctx.obj)
    spec_file_content = {"stack": stack}
    if default_spec_file_content:
        spec_file_content.update(default_spec_file_content)
    if verbose:
        print(f"Creating spec file for stack: {stack}")

    ports = _get_ports(stack)
    if ports:
        spec_file_content["ports"] = ports

    named_volumes = _get_named_volumes(stack)
    if named_volumes:
        volume_descriptors = {}
        for named_volume in named_volumes:
            volume_descriptors[named_volume] = f"./data/{named_volume}"
        spec_file_content["volumes"] = volume_descriptors

    with open(output, "w") as output_file:
        yaml.dump(spec_file_content, output_file)


@click.command()
@click.option("--spec-file", required=True, help="Spec file to use to create this deployment")
@click.option("--deployment-dir", help="Create deployment files in this directory")
@click.pass_context
def create(ctx, spec_file, deployment_dir):
    # This function fails with a useful error message if the file doens't exist
    parsed_spec = get_parsed_deployment_spec(spec_file)
    stack_name = parsed_spec['stack']
    stack_file = get_stack_file_path(stack_name)
    parsed_stack = get_parsed_stack_config(stack_name)
    if global_options(ctx).debug:
        print(f"parsed spec: {parsed_spec}")
    if deployment_dir is None:
        deployment_dir = _make_default_deployment_dir()
    if os.path.exists(deployment_dir):
        print(f"Error: {deployment_dir} already exists")
        sys.exit(1)
    os.mkdir(deployment_dir)
    # Copy spec file and the stack file into the deployment dir
    copyfile(spec_file, os.path.join(deployment_dir, os.path.basename(spec_file)))
    copyfile(stack_file, os.path.join(deployment_dir, os.path.basename(stack_file)))
    # Copy the pod files into the deployment dir, fixing up content
    pods = parsed_stack['pods']
    destination_compose_dir = os.path.join(deployment_dir, "compose")
    os.mkdir(destination_compose_dir)
    data_dir = Path(__file__).absolute().parent.joinpath("data")
    yaml = get_yaml()
    for pod in pods:
        pod_file_path = os.path.join(get_compose_file_dir(), f"docker-compose-{pod}.yml")
        parsed_pod_file = yaml.load(open(pod_file_path, "r"))
        extra_config_dirs = _find_extra_config_dirs(parsed_pod_file, pod)
        if global_options(ctx).debug:
            print(f"extra config dirs: {extra_config_dirs}")
        _fixup_pod_file(parsed_pod_file, parsed_spec, destination_compose_dir)
        with open(os.path.join(destination_compose_dir, os.path.basename(pod_file_path)), "w") as output_file:
            yaml.dump(parsed_pod_file, output_file)
        # Copy the config files for the pod, if any
        config_dirs = {pod}
        config_dirs = config_dirs.union(extra_config_dirs)
        for config_dir in config_dirs:
            source_config_dir = data_dir.joinpath("config", config_dir)
            if os.path.exists(source_config_dir):
                destination_config_dir = os.path.join(deployment_dir, "config", config_dir)
                # If the same config dir appears in multiple pods, it may already have been copied
                if not os.path.exists(destination_config_dir):
                    copytree(source_config_dir, destination_config_dir)
    # Delegate to the stack's Python code
    # The deploy create command doesn't require a --stack argument so we need to insert the
    # stack member here.
    deployment_command_context = ctx.obj
    deployment_command_context.stack = stack_name
    deployment_context = DeploymentContext(Path(deployment_dir), deployment_command_context)
    call_stack_deploy_create(deployment_context)


@click.command()
@click.option("--node-moniker", help="Help goes here")
@click.option("--key-name", help="Help goes here")
@click.option("--initialize-network", is_flag=True, default=False, help="Help goes here")
@click.option("--join-network", is_flag=True, default=False, help="Help goes here")
@click.option("--create-network", is_flag=True, default=False, help="Help goes here")
@click.argument('extra_args', nargs=-1)
@click.pass_context
def setup(ctx, node_moniker, key_name, initialize_network, join_network, create_network, extra_args):
    call_stack_deploy_setup(ctx.obj, extra_args)
