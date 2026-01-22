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

from abc import ABC, abstractmethod
from pathlib import Path


class Deployer(ABC):
    @abstractmethod
    def up(self, detach, skip_cluster_management, services):
        pass

    @abstractmethod
    def down(self, timeout, volumes, skip_cluster_management):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def ps(self):
        pass

    @abstractmethod
    def status(self):
        pass

    @abstractmethod
    def port(self, service, private_port):
        pass

    @abstractmethod
    def execute(self, service_name, command, tty, envs):
        pass

    @abstractmethod
    def logs(self, services, tail, follow, stream):
        pass

    @abstractmethod
    def run(
        self,
        image: str,
        command=None,
        user=None,
        volumes=None,
        entrypoint=None,
        env={},
        ports=[],
        detach=False,
    ):
        pass

    @abstractmethod
    def run_job(self, job_name: str, release_name: str = None):
        pass


class DeployerException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class DeployerConfigGenerator(ABC):
    @abstractmethod
    def generate(self, deployment_dir: Path):
        pass
