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

import hashlib
import os
from pathlib import Path

from stack_orchestrator import constants
from stack_orchestrator.util import get_yaml
from stack_orchestrator.deploy.stack import Stack
from stack_orchestrator.deploy.spec import Spec


class DeploymentContext:
    deployment_dir: Path
    id: str
    spec: Spec
    stack: Stack

    def get_stack_file(self):
        return self.deployment_dir.joinpath(constants.stack_file_name)

    def get_spec_file(self):
        return self.deployment_dir.joinpath(constants.spec_file_name)

    def get_env_file(self):
        return self.deployment_dir.joinpath(constants.config_file_name)

    def get_deployment_file(self):
        return self.deployment_dir.joinpath(constants.deployment_file_name)

    def get_compose_dir(self):
        return self.deployment_dir.joinpath(constants.compose_dir_name)

    def get_cluster_id(self):
        return self.id

    def init(self, dir):
        self.deployment_dir = dir
        self.spec = Spec()
        self.spec.init_from_file(self.get_spec_file())
        self.stack = Stack(self.spec.obj["stack"])
        self.stack.init_from_file(self.get_stack_file())
        deployment_file_path = self.get_deployment_file()
        if deployment_file_path.exists():
            obj = get_yaml().load(open(deployment_file_path, "r"))
            self.id = obj[constants.cluster_id_key]
        # Handle the case of a legacy deployment with no file
        # Code below is intended to match the output from _make_default_cluster_name()
        # TODO: remove when we no longer need to support legacy deployments
        else:
            path = os.path.realpath(os.path.abspath(self.get_compose_dir()))
            unique_cluster_descriptor = f"{path},{self.get_stack_file()},None,None"
            hash = hashlib.md5(unique_cluster_descriptor.encode()).hexdigest()[:16]
            self.id = f"{constants.cluster_name_prefix}{hash}"
