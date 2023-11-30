
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

from stack_orchestrator import constants
from stack_orchestrator.deploy.stack import Stack
from stack_orchestrator.deploy.spec import Spec


class DeploymentContext:
    deployment_dir: Path
    spec: Spec
    stack: Stack

    def get_stack_file(self):
        return self.deployment_dir.joinpath(constants.stack_file_name)

    def get_spec_file(self):
        return self.deployment_dir.joinpath(constants.spec_file_name)

    def get_env_file(self):
        return self.deployment_dir.joinpath(constants.config_file_name)

    # TODO: implement me
    def get_cluster_name(self):
        return None

    def init(self, dir):
        self.deployment_dir = dir
        self.spec = Spec()
        self.spec.init_from_file(self.get_spec_file())
        self.stack = Stack(self.spec.obj["stack"])
        self.stack.init_from_file(self.get_stack_file())
