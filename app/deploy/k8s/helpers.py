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

from kubernetes import client
import subprocess
from typing import Set

from app.opts import opts


def _run_command(command: str):
    if opts.o.debug:
        print(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    if opts.o.debug:
        print(f"Result: {result}")


def create_cluster(name: str):
    _run_command(f"kind create cluster --name {name}")


def destroy_cluster(name: str):
    _run_command(f"kind delete cluster --name {name}")


def load_images_into_kind(kind_cluster_name: str, image_set: Set[str]):
    for image in image_set:
        _run_command(f"kind load docker-image {image} --name {kind_cluster_name}")


def pods_in_deployment(api: client.AppsV1Api, deployment_name: str):
    # See: https://stackoverflow.com/a/73525759/1701505
    deployment_info = api.read_namespaced_deployment(deployment_name, "default")
    if opts.o.debug:
        print(f"deployment: {deployment_info}")
    return []