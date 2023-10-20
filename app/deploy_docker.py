# Copyright © 2022, 2023 Vulcanize

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

from python_on_whales import DockerClient, DockerException
from app.deployer import Deployer


class DockerDeployer(Deployer):
    def __init__(self, compose_files, compose_project_name, compose_env_file) -> None:
        self.docker = DockerClient(compose_files=compose_files, compose_project_name=compose_project_name,
                                   compose_env_file=compose_env_file)

    def compose_up(self, detach, services):
        return self.docker.compose.up(detach=detach, services=services)

    def compose_down(self, timeout, volumes):
        return self.docker.compose.down(timeout=timeout, volumes=volumes)

    def compose_ps(self):
        return self.docker.compose.ps()

    def compose_port(self, service, private_port):
        return self.docker.compose.port(service=service, private_port=private_port)

    def compose_execute(self, service_name, command, envs):
        return self.docker.compose.execute(service_name=service_name, command=command, envs=envs)

    def compose_logs(self, services, tail, follow, stream):
        return self.docker.compose.logs(services=services, tail=tail, follow=follow, stream=stream)
