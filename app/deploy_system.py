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

def include_exclude_check(s, args):
    if args.include == None and args.exclude == None:
        return True
    if args.include != None:
        include_list = args.include.split(",")
        return s in include_list
    if args.exclude != None:
        exclude_list = args.exclude.split(",")
        return s not in exclude_list

parser = argparse.ArgumentParser(
    description="deploy the complete stack"
    )
parser.add_argument("command", type=str, nargs=1, choices=['up', 'down', 'ps'], help="command: up|down|ps")
parser.add_argument("--verbose", action="store_true", help="increase output verbosity")
parser.add_argument("--quiet", action="store_true", help="don\'t print informational output")
parser.add_argument("--check-only", action="store_true", help="looks at what\'s already there and checks if it looks good")
parser.add_argument("--dry-run", action="store_true", help="don\'t do anything, just print the commands that would be executed")
group = parser.add_mutually_exclusive_group()
group.add_argument("--exclude", type=str, help="don\'t start these components")
group.add_argument("--include", type=str, help="only start these components")

args = parser.parse_args()

verbose = args.verbose
quiet = args.quiet

@click.command()
def command():

    with open("cluster-list.txt") as cluster_list_file:
        clusters = cluster_list_file.read().splitlines()

    if verbose:
        print(f'Cluster components: {clusters}')

    # Construct a docker compose command suitable for our purpose

    compose_files = []
    for cluster in clusters:
        if include_exclude_check(cluster, args):
            compose_file_name = os.path.join("compose", f"docker-compose-{cluster}.yml")
            compose_files.append(compose_file_name)
        else:
            if not quiet:
                print(f"Excluding: {cluster}")

    if verbose:
        print(f"files: {compose_files}")

    # See: https://gabrieldemarmiesse.github.io/python-on-whales/sub-commands/compose/
    docker = DockerClient(compose_files=compose_files)

    command = args.command[0]
    if not args.dry_run:
        if command == "up":
            if verbose:
                print("Running compose up")
            docker.compose.up(detach=True)
        elif command == "down":
            if verbose:
                print("Running compose down")
            docker.compose.down()
