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

from app.deploy_k8s import K8sDeployer
from app.deploy_docker import DockerDeployer


def getDeployer(type, compose_files, compose_project_name, compose_env_file):
    if type == "compose" or type is None:
        return DockerDeployer(compose_files, compose_project_name, compose_env_file)
    elif type == "k8s":
        return K8sDeployer(compose_files, compose_project_name, compose_env_file)
    else:
        print(f"ERROR: deploy-to {type} is not valid")
