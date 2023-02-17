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

# Deploys the system components using docker-compose

import hashlib
import os
import sys
from decouple import config
import subprocess
from python_on_whales import DockerClient
import click
import importlib.resources
from pathlib import Path
from .util import include_exclude_check, get_parsed_stack_config


@click.command()
@click.option("--include", help="only start these components")
@click.option("--exclude", help="don\'t start these components")
@click.option("--cluster", help="specify a non-default cluster name")
@click.argument('command', required=True)  # help: command: up|down|ps
@click.argument('extra_args', nargs=-1)  # help: command: up|down|ps <service1> <service2>
@click.pass_context
def command(ctx, include, exclude, cluster, command, extra_args):
    '''deploy a stack'''

    # TODO: implement option exclusion and command value constraint lost with the move from argparse to click

    debug = ctx.obj.debug
    quiet = ctx.obj.quiet
    verbose = ctx.obj.verbose
    local_stack = ctx.obj.local_stack
    dry_run = ctx.obj.dry_run
    stack = ctx.obj.stack

    if local_stack:
        dev_root_path = os.getcwd()[0:os.getcwd().rindex("stack-orchestrator")]
        print(f'Local stack dev_root_path (CERC_REPO_BASE_DIR) overridden to: {dev_root_path}')
    else:
        dev_root_path = os.path.expanduser(config("CERC_REPO_BASE_DIR", default="~/cerc"))

    # See: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure
    compose_dir = Path(__file__).absolute().parent.joinpath("data", "compose")

    if cluster is None:
        # Create default unique, stable cluster name from confile file path
        # TODO: change this to the config file path
        path = os.path.realpath(sys.argv[0])
        hash = hashlib.md5(path.encode()).hexdigest()
        cluster = f"laconic-{hash}"
        if verbose:
            print(f"Using cluster name: {cluster}")

    # See: https://stackoverflow.com/a/20885799/1701505
    from . import data
    with importlib.resources.open_text(data, "pod-list.txt") as pod_list_file:
        all_pods = pod_list_file.read().splitlines()

    pods_in_scope = []
    if stack:
        stack_config = get_parsed_stack_config(stack)
        # TODO: syntax check the input here
        pods_in_scope = stack_config['pods']
    else:
        pods_in_scope = all_pods

    # Convert all pod definitions to v1.1 format
    pods_in_scope = _convert_to_new_format(pods_in_scope)

    if verbose:
        print(f"Pods: {pods_in_scope}")

    # Construct a docker compose command suitable for our purpose

    compose_files = []
    pre_start_commands = []
    post_start_commands = []
    for pod in pods_in_scope:
        pod_name = pod["name"]
        pod_repository = pod["repository"]
        pod_path = pod["path"]
        if include_exclude_check(pod_name, include, exclude):
            if pod_repository is None or pod_repository == "internal":
                compose_file_name = os.path.join(compose_dir, f"docker-compose-{pod_path}.yml")
            else:
                pod_root_dir = os.path.join(dev_root_path, pod_repository.split("/")[-1], pod["path"])
                compose_file_name = os.path.join(pod_root_dir, "docker-compose.yml")
                pod_pre_start_command = pod["pre_start_command"]
                pod_post_start_command = pod["post_start_command"]
                if pod_pre_start_command is not None:
                    pre_start_commands.append(os.path.join(pod_root_dir, pod_pre_start_command))
                if pod_post_start_command is not None:
                    post_start_commands.append(os.path.join(pod_root_dir, pod_post_start_command))
            compose_files.append(compose_file_name)
        else:
            if verbose:
                print(f"Excluding: {pod_name}")

    if verbose:
        print(f"files: {compose_files}")

    # See: https://gabrieldemarmiesse.github.io/python-on-whales/sub-commands/compose/
    docker = DockerClient(compose_files=compose_files, compose_project_name=cluster)

    extra_args_list = list(extra_args) or None

    if not dry_run:
        if command == "up":
            if debug:
                os.environ["CERC_SCRIPT_DEBUG"] = "true"
            if verbose:
                print(f"Running compose up for extra_args: {extra_args_list}")
            for pre_start_command in pre_start_commands:
                _run_command(ctx.obj, cluster, pre_start_command)
            docker.compose.up(detach=True, services=extra_args_list)
            for post_start_command in post_start_commands:
                _run_command(ctx.obj, cluster, post_start_command)
        elif command == "down":
            if verbose:
                print("Running compose down")
            docker.compose.down()
        elif command == "exec":
            if extra_args_list is None or len(extra_args_list) < 2:
                print("Usage: exec <service> <cmd>")
                sys.exit(1)
            service_name = extra_args_list[0]
            command_to_exec = extra_args_list[1:]
            container_exec_env = {
                "CERC_SCRIPT_DEBUG": "true"
            } if debug else {}
            if verbose:
                print(f"Running compose exec {service_name} {command_to_exec}")
            docker.compose.execute(service_name, command_to_exec, envs=container_exec_env)
        elif command == "port":
            if extra_args_list is None or len(extra_args_list) < 2:
                print("Usage: port <service> <exposed-port>")
                sys.exit(1)
            service_name = extra_args_list[0]
            exposed_port = extra_args_list[1]
            if verbose:
                print(f"Running compose port {service_name} {exposed_port}")
            mapped_port_data = docker.compose.port(service_name, exposed_port)
            print(f"{mapped_port_data[0]}:{mapped_port_data[1]}")
        elif command == "ps":
            if verbose:
                print("Running compose ps")
            container_list = docker.compose.ps()
            if len(container_list) > 0:
                print("Running containers:")
                for container in container_list:
                    print(f"id: {container.id}, name: {container.name}, ports: ", end="")
                    ports = container.network_settings.ports
                    comma = ""
                    for port_mapping in ports.keys():
                        mapping = ports[port_mapping]
                        print(comma, end="")
                        if mapping is None:
                            print(f"{port_mapping}", end="")
                        else:
                            print(f"{mapping[0]['HostIp']}:{mapping[0]['HostPort']}->{port_mapping}", end="")
                        comma = ", "
                    print()
            else:
                print("No containers running")
        elif command == "logs":
            if verbose:
                print("Running compose logs")
            docker.compose.logs()


def _convert_to_new_format(old_pod_array):
    new_pod_array = []
    for old_pod in old_pod_array:
        if isinstance(old_pod, dict):
            new_pod_array.append(old_pod)
        else:
            new_pod = {
                "name": old_pod,
                "repository": "internal",
                "path": old_pod
            }
            new_pod_array.append(new_pod)
    return new_pod_array


def _run_command(ctx, cluster_name, command):
    if ctx.verbose:
        print(f"Running command: {command}")
    command_dir = os.path.dirname(command)
    print(f"command_dir: {command_dir}")
    command_file = os.path.join(".", os.path.basename(command))
    command_env = os.environ.copy()
    command_env["CERC_SO_COMPOSE_PROJECT"] = cluster_name
    if ctx.debug:
        command_env["CERC_SCRIPT_DEBUG"] = "true"
    command_result = subprocess.run(command_file, shell=True, env=command_env, cwd=command_dir)
    if command_result.returncode != 0:
        print(f"FATAL Error running command: {command}")
        sys.exit(1)
