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

from typing import List
from dataclasses import dataclass
from app.deploy_types import DeployCommandContext, VolumeMapping


def _container_image_from_service(service: str):
    return "cerc/test-container:local"


def _volumes_to_docker(mounts: List[VolumeMapping]):
# Example from doc: [("/", "/host"), ("/etc/hosts", "/etc/hosts", "rw")]
    result = []
    for mount in mounts:
        docker_volume = (mount.host_path, mount.container_path)
        result.append(docker_volume)
    return result


def run_container_command(ctx: DeployCommandContext, service: str, command: str, mounts: List[VolumeMapping]):
    docker = ctx.docker
    container_image = _container_image_from_service(service)
    docker_volumes = _volumes_to_docker(mounts)
    docker_output = docker.run(container_image, ["-c", command], entrypoint="bash", volumes=docker_volumes)
    # There doesn't seem to be a way to get an exit code from docker.run()
    return (docker_output, 0)
