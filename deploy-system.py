# Deploys the system components using docker-compose

import os
import argparse
from decouple import config
from python_on_whales import DockerClient

parser = argparse.ArgumentParser(
    description="deploy the complete stack"
    )
parser.add_argument("--verbose", action="store_true", help="increase output verbosity")
parser.add_argument("--quiet", action="store_true", help="don\'t print informational output")
parser.add_argument("--check-only", action="store_true", help="looks at what\'s already there and checks if it looks good")
parser.add_argument("--dry-run", action="store_true", help="don\'t do anything, just print the commands that would be executed")

args = parser.parse_args()
print(args)

verbose = args.verbose
quiet = args.quiet

with open("cluster-list.txt") as cluster_list_file:
    clusters = cluster_list_file.read().splitlines()

if verbose:
    print(f'Cluster components: {clusters}')

# Construct a docker compose command suitable for our purpose

compose_files = []
for cluster in clusters:
    compose_file_name = os.path.join("compose", f"docker-compose-{cluster}.yml")
    compose_files.append(compose_file_name)

print(f"files: {compose_files}")

# See: https://gabrieldemarmiesse.github.io/python-on-whales/sub-commands/compose/
docker = DockerClient(compose_files=compose_files)

docker.compose.up()

