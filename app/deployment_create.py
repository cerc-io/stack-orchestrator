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

import click
from importlib import util
import os
from pathlib import Path
from typing import List
import random
from shutil import copy, copyfile, copytree
import sys
from app.util import (get_stack_file_path, get_parsed_deployment_spec, get_parsed_stack_config, global_options, get_yaml,
                      get_pod_list, get_pod_file_path, pod_has_scripts, get_pod_script_paths)
from app.deploy_types import DeploymentContext, LaconicStackSetupCommand


def _make_default_deployment_dir():
    return "deployment-001"


def _get_ports(stack):
    ports = {}
    parsed_stack = get_parsed_stack_config(stack)
    pods = get_pod_list(parsed_stack)
    yaml = get_yaml()
    for pod in pods:
        pod_file_path = get_pod_file_path(parsed_stack, pod)
        parsed_pod_file = yaml.load(open(pod_file_path, "r"))
        if "services" in parsed_pod_file:
            for svc_name, svc in parsed_pod_file["services"].items():
                if "ports" in svc:
                    # Ports can appear as strings or numbers.  We normalize them as strings.
                    ports[svc_name] = [str(x) for x in svc["ports"]]
    return ports


def _get_named_volumes(stack):
    # Parse the compose files looking for named volumes
    named_volumes = []
    parsed_stack = get_parsed_stack_config(stack)
    pods = get_pod_list(parsed_stack)
    yaml = get_yaml()
    for pod in pods:
        pod_file_path = get_pod_file_path(parsed_stack, pod)
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
def call_stack_deploy_setup(deploy_command_context, parameters: LaconicStackSetupCommand, extra_args):
    # Link with the python file in the stack
    # Call a function in it
    # If no function found, return None
    python_file_path = get_stack_file_path(deploy_command_context.stack).parent.joinpath("deploy", "commands.py")
    if python_file_path.exists():
        spec = util.spec_from_file_location("commands", python_file_path)
        imported_stack = util.module_from_spec(spec)
        spec.loader.exec_module(imported_stack)
        return imported_stack.setup(deploy_command_context, parameters, extra_args)
    else:
        return None


# TODO: fold this with function above
def call_stack_deploy_create(deployment_context, extra_args):
    # Link with the python file in the stack
    # Call a function in it
    # If no function found, return None
    python_file_path = get_stack_file_path(deployment_context.command_context.stack).parent.joinpath("deploy", "commands.py")
    if python_file_path.exists():
        spec = util.spec_from_file_location("commands", python_file_path)
        imported_stack = util.module_from_spec(spec)
        spec.loader.exec_module(imported_stack)
        return imported_stack.create(deployment_context, extra_args)
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


def _get_mapped_ports(stack: str, map_recipe: str):
    port_map_recipes = ["any-variable-random", "localhost-same", "any-same", "localhost-fixed-random", "any-fixed-random"]
    ports = _get_ports(stack)
    if ports:
        # Implement any requested mapping recipe
        if map_recipe:
            if map_recipe in port_map_recipes:
                for service in ports.keys():
                    ports_array = ports[service]
                    for x in range(0, len(ports_array)):
                        orig_port = ports_array[x]
                        # Strip /udp suffix if present
                        bare_orig_port = orig_port.replace("/udp", "")
                        random_port = random.randint(20000, 50000)  # Beware: we're relying on luck to not collide
                        if map_recipe == "any-variable-random":
                            # This is the default so take no action
                            pass
                        elif map_recipe == "localhost-same":
                            # Replace instances of "- XX" with "- 127.0.0.1:XX"
                            ports_array[x] = f"127.0.0.1:{bare_orig_port}:{orig_port}"
                        elif map_recipe == "any-same":
                            # Replace instances of "- XX" with "- 0.0.0.0:XX"
                            ports_array[x] = f"0.0.0.0:{bare_orig_port}:{orig_port}"
                        elif map_recipe == "localhost-fixed-random":
                            # Replace instances of "- XX" with "- 127.0.0.1:<rnd>:XX"
                            ports_array[x] = f"127.0.0.1:{random_port}:{orig_port}"
                        elif map_recipe == "any-fixed-random":
                            # Replace instances of "- XX" with "- 0.0.0.0:<rnd>:XX"
                            ports_array[x] = f"0.0.0.0:{random_port}:{orig_port}"
                        else:
                            print("Error: bad map_recipe")
            else:
                print(f"Error: --map-ports-to-host must specify one of: {port_map_recipes}")
                sys.exit(1)
    return ports


def _parse_config_variables(variable_values: str):
    result = None
    if variable_values:
        value_pairs = variable_values.split(",")
        if len(value_pairs):
            result_values = {}
            for value_pair in value_pairs:
                variable_value_pair = value_pair.split("=")
                if len(variable_value_pair) != 2:
                    print(f"ERROR: config argument is not valid: {variable_values}")
                    sys.exit(1)
                variable_name = variable_value_pair[0]
                variable_value = variable_value_pair[1]
                result_values[variable_name] = variable_value
            result = {"config": result_values}
    return result


@click.command()
@click.option("--config", help="Provide config variables for the deployment")
@click.option("--output", required=True, help="Write yaml spec file here")
@click.option("--map-ports-to-host", required=False,
              help="Map ports to the host as one of: any-variable-random (default), "
              "localhost-same, any-same, localhost-fixed-random, any-fixed-random")
@click.pass_context
def init(ctx, config, output, map_ports_to_host):
    yaml = get_yaml()
    stack = global_options(ctx).stack
    debug = global_options(ctx).debug
    default_spec_file_content = call_stack_deploy_init(ctx.obj)
    spec_file_content = {"stack": stack}
    if default_spec_file_content:
        spec_file_content.update(default_spec_file_content)
    config_variables = _parse_config_variables(config)
    if config_variables:
        # Implement merge, since update() overwrites
        orig_config = spec_file_content["config"]
        new_config = config_variables["config"]
        merged_config = {**new_config, **orig_config}
        spec_file_content.update({"config": merged_config})
    if debug:
        print(f"Creating spec file for stack: {stack} with content: {spec_file_content}")

    ports = _get_mapped_ports(stack, map_ports_to_host)
    spec_file_content["ports"] = ports

    named_volumes = _get_named_volumes(stack)
    if named_volumes:
        volume_descriptors = {}
        for named_volume in named_volumes:
            volume_descriptors[named_volume] = f"./data/{named_volume}"
        spec_file_content["volumes"] = volume_descriptors

    with open(output, "w") as output_file:
        yaml.dump(spec_file_content, output_file)


def _write_config_file(spec_file: Path, config_env_file: Path):
    spec_content = get_parsed_deployment_spec(spec_file)
    # Note: we want to write an empty file even if we have no config variables
    with open(config_env_file, "w") as output_file:
        if "config" in spec_content and spec_content["config"]:
            config_vars = spec_content["config"]
            if config_vars:
                for variable_name, variable_value in config_vars.items():
                    output_file.write(f"{variable_name}={variable_value}\n")


def _copy_files_to_directory(file_paths: List[Path], directory: Path):
    for path in file_paths:
        # Using copy to preserve the execute bit
        copy(path, os.path.join(directory, os.path.basename(path)))


@click.command()
@click.option("--spec-file", required=True, help="Spec file to use to create this deployment")
@click.option("--deployment-dir", help="Create deployment files in this directory")
# TODO: Hack
@click.option("--network-dir", help="Network configuration supplied in this directory")
@click.option("--initial-peers", help="Initial set of persistent peers")
@click.pass_context
def create(ctx, spec_file, deployment_dir, network_dir, initial_peers):
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
    # Copy any config varibles from the spec file into an env file suitable for compose
    _write_config_file(spec_file, os.path.join(deployment_dir, "config.env"))
    # Copy the pod files into the deployment dir, fixing up content
    pods = get_pod_list(parsed_stack)
    destination_compose_dir = os.path.join(deployment_dir, "compose")
    os.mkdir(destination_compose_dir)
    destination_pods_dir = os.path.join(deployment_dir, "pods")
    os.mkdir(destination_pods_dir)
    data_dir = Path(__file__).absolute().parent.joinpath("data")
    yaml = get_yaml()
    for pod in pods:
        pod_file_path = get_pod_file_path(parsed_stack, pod)
        parsed_pod_file = yaml.load(open(pod_file_path, "r"))
        extra_config_dirs = _find_extra_config_dirs(parsed_pod_file, pod)
        destination_pod_dir = os.path.join(destination_pods_dir, pod)
        os.mkdir(destination_pod_dir)
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
        # Copy the script files for the pod, if any
        if pod_has_scripts(parsed_stack, pod):
            destination_script_dir = os.path.join(destination_pod_dir, "scripts")
            os.mkdir(destination_script_dir)
            script_paths = get_pod_script_paths(parsed_stack, pod)
            _copy_files_to_directory(script_paths, destination_script_dir)
    # Delegate to the stack's Python code
    # The deploy create command doesn't require a --stack argument so we need to insert the
    # stack member here.
    deployment_command_context = ctx.obj
    deployment_command_context.stack = stack_name
    deployment_context = DeploymentContext(Path(deployment_dir), deployment_command_context)
    call_stack_deploy_create(deployment_context, [network_dir, initial_peers])


# TODO: this code should be in the stack .py files but
# we haven't yet figured out how to integrate click across
# the plugin boundary
@click.command()
@click.option("--node-moniker", help="Moniker for this node")
@click.option("--chain-id", help="The new chain id")
@click.option("--key-name", help="Name for new node key")
@click.option("--gentx-files", help="List of comma-delimited gentx filenames from other nodes")
@click.option("--genesis-file", help="Genesis file for the network")
@click.option("--initialize-network", is_flag=True, default=False, help="Initialize phase")
@click.option("--join-network", is_flag=True, default=False, help="Join phase")
@click.option("--create-network", is_flag=True, default=False, help="Create phase")
@click.option("--network-dir", help="Directory for network files")
@click.argument('extra_args', nargs=-1)
@click.pass_context
def setup(ctx, node_moniker, chain_id, key_name, gentx_files, genesis_file, initialize_network, join_network, create_network,
          network_dir, extra_args):
    parmeters = LaconicStackSetupCommand(chain_id, node_moniker, key_name, initialize_network, join_network, create_network,
                                         gentx_files, genesis_file, network_dir)
    call_stack_deploy_setup(ctx.obj, parmeters, extra_args)
