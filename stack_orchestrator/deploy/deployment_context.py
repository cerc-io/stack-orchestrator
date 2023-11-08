
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

from stack_orchestrator.deploy.stack import Stack
from stack_orchestrator.deploy.spec import Spec


class DeploymentContext:
    dir: Path
    spec: Spec
    stack: Stack

    def get_stack_file(self):
        return self.dir.joinpath("stack.yml")

    def get_spec_file(self):
        return self.dir.joinpath("spec.yml")

    def get_env_file(self):
        return self.dir.joinpath("config.env")

    # TODO: implement me
    def get_cluster_name(self):
        return None

    def init(self, dir):
        self.dir = dir
        self.stack = Stack()
        self.stack.init_from_file(self.get_stack_file())
        self.spec = Spec()
        self.spec.init_from_file(self.get_spec_file())
