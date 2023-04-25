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
import copy
import os
import sys
from dataclasses import dataclass
from decouple import config
import subprocess
from python_on_whales import DockerClient, DockerException
import click
import importlib.resources
from pathlib import Path
from .util import include_exclude_check, get_parsed_stack_config


@click.command()
@click.option("--include", help="only start these components")
@click.option("--exclude", help="don\'t start these components")
@click.option("--env-file", help="env file to be used")
@click.option("--cluster", help="specify a non-default cluster name")
@click.argument('command', required=True)  # help: command: up|down|ps
@click.argument('extra_args', nargs=-1)  # help: command: up|down|ps <service1> <service2>
@click.pass_context
def command(ctx, include, exclude, env_file, cluster, command, extra_args):
    '''deploy a stack'''

    # TODO: implement option exclusion and command value constraint lost with the move from argparse to click

    debug = ctx.obj.debug
    quiet = ctx.obj.quiet
    verbose = ctx.obj.verbose
    local_stack = ctx.obj.local_stack
    dry_run = ctx.obj.dry_run
    stack = ctx.obj.stack

    cluster_context = _make_cluster_context(ctx.obj, include, exclude, cluster)

    # See: https://gabrieldemarmiesse.github.io/python-on-whales/sub-commands/compose/
    docker = DockerClient(compose_files=cluster_context.compose_files, compose_project_name=cluster_context.cluster, compose_env_file=env_file)

    extra_args_list = list(extra_args) or None

    if not dry_run:
        if command == "up":
            container_exec_env = _make_runtime_env(ctx.obj)
            for attr, value in container_exec_env.items():
                os.environ[attr] = value
            if verbose:
                print(f"Running compose up with container_exec_env: {container_exec_env}, extra_args: {extra_args_list}")
            for pre_start_command in cluster_context.pre_start_commands:
                _run_command(ctx.obj, cluster_context.cluster, pre_start_command)
            docker.compose.up(detach=True, services=extra_args_list)
            for post_start_command in cluster_context.post_start_commands:
                _run_command(ctx.obj, cluster_context.cluster, post_start_command)

            _orchestrate_cluster_config(ctx.obj, cluster_context.config, docker, container_exec_env)

        elif command == "down":
            if verbose:
                print("Running compose down")

            timeout_arg = None
            if extra_args_list:
                timeout_arg=extra_args_list[0]

            # Specify shutdown timeout (default 10s) to give services enough time to shutdown gracefully
            docker.compose.down(timeout=timeout_arg)
        elif command == "exec":
            if extra_args_list is None or len(extra_args_list) < 2:
                print("Usage: exec <service> <cmd>")
                sys.exit(1)
            service_name = extra_args_list[0]
            command_to_exec = ["sh", "-c"] + extra_args_list[1:]
            container_exec_env = _make_runtime_env(ctx.obj)
            if verbose:
                print(f"Running compose exec {service_name} {command_to_exec}")
            try:
                docker.compose.execute(service_name, command_to_exec, envs=container_exec_env)
            except DockerException as error:
                print(f"container command returned error exit status")
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
            logs_output = docker.compose.logs(services=extra_args_list if extra_args_list is not None else [])
            print(logs_output)


def get_stack_status(ctx, stack):

    ctx_copy = copy.copy(ctx)
    ctx_copy.stack = stack

    cluster_context = _make_cluster_context(ctx_copy, None, None, None)
    docker = DockerClient(compose_files=cluster_context.compose_files, compose_project_name=cluster_context.cluster)
    # TODO: refactor to avoid duplicating this code above
    if ctx.verbose:
        print("Running compose ps")
    container_list = docker.compose.ps()
    if len(container_list) > 0:
        if ctx.debug:
            print(f"Container list from compose ps: {container_list}")
        return True
    else:
        if ctx.debug:
            print("No containers found from compose ps")
        False


def _make_runtime_env(ctx):
    container_exec_env = {
        "CERC_HOST_UID": f"{os.getuid()}",
        "CERC_HOST_GID": f"{os.getgid()}"
    }
    container_exec_env.update({"CERC_SCRIPT_DEBUG": "true"} if ctx.debug else {})
    return container_exec_env


def _make_cluster_context(ctx, include, exclude, cluster):

    if ctx.local_stack:
        dev_root_path = os.getcwd()[0:os.getcwd().rindex("stack-orchestrator")]
        print(f'Local stack dev_root_path (CERC_REPO_BASE_DIR) overridden to: {dev_root_path}')
    else:
        dev_root_path = os.path.expanduser(config("CERC_REPO_BASE_DIR", default="~/cerc"))

    # See: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure
    compose_dir = Path(__file__).absolute().parent.joinpath("data", "compose")

    if cluster is None:
        # Create default unique, stable cluster name from confile file path and stack name if provided
        # TODO: change this to the config file path
        path = os.path.realpath(sys.argv[0])
        unique_cluster_descriptor = f"{path},{ctx.stack},{include},{exclude}"
        if ctx.debug:
            print(f"pre-hash descriptor: {unique_cluster_descriptor}")
        hash = hashlib.md5(unique_cluster_descriptor.encode()).hexdigest()
        cluster = f"laconic-{hash}"
        if ctx.verbose:
            print(f"Using cluster name: {cluster}")

    # See: https://stackoverflow.com/a/20885799/1701505
    from . import data
    with importlib.resources.open_text(data, "pod-list.txt") as pod_list_file:
        all_pods = pod_list_file.read().splitlines()

    pods_in_scope = []
    if ctx.stack:
        stack_config = get_parsed_stack_config(ctx.stack)
        # TODO: syntax check the input here
        pods_in_scope = stack_config['pods']
        cluster_config = stack_config['config'] if 'config' in stack_config else None
    else:
        pods_in_scope = all_pods
        cluster_config = None

    # Convert all pod definitions to v1.1 format
    pods_in_scope = _convert_to_new_format(pods_in_scope)

    if ctx.verbose:
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
            if ctx.verbose:
                print(f"Excluding: {pod_name}")

    if ctx.verbose:
        print(f"files: {compose_files}")

    return cluster_context(cluster, compose_files, pre_start_commands, post_start_commands, cluster_config)


class cluster_context:
    def __init__(self, cluster, compose_files, pre_start_commands, post_start_commands, config) -> None:
        self.cluster = cluster
        self.compose_files = compose_files
        self.pre_start_commands = pre_start_commands
        self.post_start_commands = post_start_commands
        self.config = config


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
    command_file = os.path.join(".", os.path.basename(command))
    command_env = os.environ.copy()
    command_env["CERC_SO_COMPOSE_PROJECT"] = cluster_name
    if ctx.debug:
        command_env["CERC_SCRIPT_DEBUG"] = "true"
    command_result = subprocess.run(command_file, shell=True, env=command_env, cwd=command_dir)
    if command_result.returncode != 0:
        print(f"FATAL Error running command: {command}")
        sys.exit(1)


def _orchestrate_cluster_config(ctx, cluster_config, docker, container_exec_env):

    @dataclass
    class ConfigDirective:
        source_container: str
        source_variable: str
        destination_container: str
        destination_variable: str

    if cluster_config is not None:
        for container in cluster_config:
            container_config = cluster_config[container]
            if ctx.verbose:
                print(f"{container} config: {container_config}")
            for directive in container_config:
                pd = ConfigDirective(
                    container_config[directive].split(".")[0],
                    container_config[directive].split(".")[1],
                    container,
                    directive
                )
                if ctx.verbose:
                    print(f"Setting {pd.destination_container}.{pd.destination_variable}"
                          f" = {pd.source_container}.{pd.source_variable}")
                # TODO: add a timeout
                waiting_for_data = True
                while waiting_for_data:
                    # TODO: fix the script paths so they're consistent between containers
                    source_value = None
                    try:
                        source_value = docker.compose.execute(pd.source_container,
                                                              ["sh", "-c",
                                                                  "sh /docker-entrypoint-scripts.d/export-"
                                                                  f"{pd.source_variable}.sh"],
                                                              tty=False,
                                                              envs=container_exec_env)
                    except DockerException as error:
                        if ctx.debug:
                            print(f"Docker exception reading config source: {error}")
                        # If the script executed failed for some reason, we get:
                        # "It returned with code 1"
                        if "It returned with code 1" in str(error):
                            if ctx.verbose:
                                print("Config export script returned an error, re-trying")
                        # If the script failed to execute (e.g. the file is not there) then we get:
                        # "It returned with code 2"
                        if "It returned with code 2" in str(error):
                            print(f"Fatal error reading config source: {error}")
                    if source_value:
                        if ctx.debug:
                            print(f"fetched source value: {source_value}")
                        destination_output = docker.compose.execute(pd.destination_container,
                                                                    ["sh", "-c",
                                                                        f"sh /scripts/import-{pd.destination_variable}.sh"
                                                                        f" {source_value}"],
                                                                    tty=False,
                                                                    envs=container_exec_env)
                        waiting_for_data = False
                    if ctx.debug:
                        print(f"destination output: {destination_output}")
