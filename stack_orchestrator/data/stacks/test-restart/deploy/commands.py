# Copyright © 2026 Vulcanize

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

from stack_orchestrator.util import get_yaml
from stack_orchestrator.deploy.deployment_context import DeploymentContext

default_spec_file_content = ""


def init(command_context):
    return get_yaml().load(default_spec_file_content)


def start(deployment_context: DeploymentContext):
    # Writes a marker file the e2e test asserts on. The test flips the
    # literal below from "v1" to "v2" in the stack-source working tree
    # before running 'deployment restart' to verify the updated hook is
    # copied into deployment_dir/hooks/ and re-executed.
    marker = deployment_context.deployment_dir / "marker"
    marker.write_text("v1")
