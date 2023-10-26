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
