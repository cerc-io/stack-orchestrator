# Copyright © 2023 Cerc

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
from pathlib import Path
from python_on_whales import DockerClient

@dataclass
class ClusterContext:
    cluster: str
    compose_files: List[str]
    pre_start_commands: List[str]
    post_start_commands: List[str]
    config: str
    env_file: str


@dataclass
class DeployCommandContext:
    cluster_context: ClusterContext
    docker: DockerClient


@dataclass
class DeploymentContext:
    stack: str
    deployment_dir: Path
    command_context: DeployCommandContext


@dataclass
class VolumeMapping:
    host_path: str
    container_path: str
