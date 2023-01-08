# Copyright © 2022 Cerc

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
from python_on_whales import DockerClient
import click
import importlib
from .util import include_exclude_check


@click.command()
@click.option("--include", help="only start these components")
@click.option("--exclude", help="don\'t start these components")
@click.option("--cluster", help="specify a non-default cluster name")
@click.argument('command', required=True)  # help: command: up|down|ps
@click.argument('services', nargs=-1)  # help: command: up|down|ps <service1> <service2>
@click.pass_context
def command(ctx, include, exclude, cluster, command, services):
    '''deploy a stack'''

    # TODO: implement option exclusion and command value constraint lost with the move from argparse to click

    quiet = ctx.obj.quiet
    verbose = ctx.obj.verbose
    dry_run = ctx.obj.dry_run

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
        pods = pod_list_file.read().splitlines()

    if verbose:
        print(f"Pods: {pods}")

    # Construct a docker compose command suitable for our purpose

    compose_files = []
    for pod in pods:
        if include_exclude_check(pod, include, exclude):
            compose_file_name = os.path.join("compose", f"docker-compose-{pod}.yml")
            compose_files.append(compose_file_name)
        else:
            if verbose:
                print(f"Excluding: {pod}")

    if verbose:
        print(f"files: {compose_files}")

    # See: https://gabrieldemarmiesse.github.io/python-on-whales/sub-commands/compose/
    docker = DockerClient(compose_files=compose_files, compose_project_name=cluster)

    services_list = list(services) or None

    if not dry_run:
        if command == "up":
            if verbose:
                print(f"Running compose up for services: {services_list}")
            docker.compose.up(detach=True, services=services_list)
        elif command == "down":
            if verbose:
                print("Running compose down")
            docker.compose.down()
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
