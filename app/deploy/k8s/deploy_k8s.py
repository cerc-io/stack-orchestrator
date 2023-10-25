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

from kubernetes import client, config
from app.deploy.deployer import Deployer


class K8sDeployer(Deployer):
    name: str = "k8s"

    def __init__(self, compose_files, compose_project_name, compose_env_file) -> None:
        config.load_kube_config()
        self.client = client.CoreV1Api()

    def up(self, detach, services):
        pass

    def down(self, timeout, volumes):
        pass

    def ps(self):
        pass

    def port(self, service, private_port):
        pass

    def execute(self, service_name, command, envs):
        pass

    def logs(self, services, tail, follow, stream):
        pass

    def run(self, image, command, user, volumes, entrypoint=None):
        pass
