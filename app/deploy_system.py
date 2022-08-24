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

import os
import argparse
from decouple import config
from python_on_whales import DockerClient
import click

def include_exclude_check(s, include, exclude):
    if include == None and exclude == None:
        return True
    if include != None:
        include_list = include.split(",")
        return s in include_list
    if exclude != None:
        exclude_list = exclude.split(",")
        return s not in exclude_list

@click.command()
@click.option('--include', help="only start these components")
@click.option('--exclude', help="don\'t start these components")
@click.argument('command') # help: command: up|down|ps
@click.pass_context
def command(ctx, include, exclude, command):
    '''deploy a stack'''

    # TODO: implement option exclusion and command value constraint lost with the move from argparse to click

    quiet = ctx.obj.quiet
    verbose = ctx.obj.verbose
    dry_run = ctx.obj.verbose

    with open("cluster-list.txt") as cluster_list_file:
        clusters = cluster_list_file.read().splitlines()

    if verbose:
        print(f'Cluster components: {clusters}')

    # Construct a docker compose command suitable for our purpose

    compose_files = []
    for cluster in clusters:
        if include_exclude_check(cluster, include, exclude):
            compose_file_name = os.path.join("compose", f"docker-compose-{cluster}.yml")
            compose_files.append(compose_file_name)
        else:
            if not quiet:
                print(f"Excluding: {cluster}")

    if verbose:
        print(f"files: {compose_files}")

    # See: https://gabrieldemarmiesse.github.io/python-on-whales/sub-commands/compose/
    docker = DockerClient(compose_files=compose_files)

    if not dry_run:
        if command == "up":
            if verbose:
                print("Running compose up")
            docker.compose.up(detach=True)
        elif command == "down":
            if verbose:
                print("Running compose down")
            docker.compose.down()
