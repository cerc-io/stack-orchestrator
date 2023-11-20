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

from pathlib import Path
from python_on_whales import DockerClient, DockerException
from stack_orchestrator.deploy.deployer import Deployer, DeployerException, DeployerConfigGenerator


class DockerDeployer(Deployer):
    name: str = "compose"
    type: str

    def __init__(self, type, deployment_dir, compose_files, compose_project_name, compose_env_file) -> None:
        self.docker = DockerClient(compose_files=compose_files, compose_project_name=compose_project_name,
                                   compose_env_file=compose_env_file)
        self.type = type

    def up(self, detach, services):
        try:
            return self.docker.compose.up(detach=detach, services=services)
        except DockerException as e:
            raise DeployerException(e)

    def down(self, timeout, volumes):
        try:
            return self.docker.compose.down(timeout=timeout, volumes=volumes)
        except DockerException as e:
            raise DeployerException(e)

    def ps(self):
        try:
            return self.docker.compose.ps()
        except DockerException as e:
            raise DeployerException(e)

    def port(self, service, private_port):
        try:
            return self.docker.compose.port(service=service, private_port=private_port)
        except DockerException as e:
            raise DeployerException(e)

    def execute(self, service, command, tty, envs):
        try:
            return self.docker.compose.execute(service=service, command=command, tty=tty, envs=envs)
        except DockerException as e:
            raise DeployerException(e)

    def logs(self, services, tail, follow, stream):
        try:
            return self.docker.compose.logs(services=services, tail=tail, follow=follow, stream=stream)
        except DockerException as e:
            raise DeployerException(e)

    def run(self, image: str, command=None, user=None, volumes=None, entrypoint=None, env={}, detach=False):
        try:
            return self.docker.run(image=image, command=command, user=user, volumes=volumes,
                                   entrypoint=entrypoint, envs=env, detach=detach, publish_all=True)
        except DockerException as e:
            raise DeployerException(e)


class DockerDeployerConfigGenerator(DeployerConfigGenerator):

    def __init__(self, type: str) -> None:
        super().__init__()

    # Nothing needed at present for the docker deployer
    def generate(self, deployment_dir: Path):
        pass
