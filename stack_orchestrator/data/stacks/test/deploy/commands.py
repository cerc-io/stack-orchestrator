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

from stack_orchestrator.util import get_yaml
from stack_orchestrator.deploy.deploy_types import DeployCommandContext
from stack_orchestrator.deploy.deployment_context import DeploymentContext
from stack_orchestrator.deploy.stack_state import State
from stack_orchestrator.deploy.deploy_util import VolumeMapping, run_container_command
from pathlib import Path

default_spec_file_content = """config:
    test-variable-1: test-value-1
"""


# Output a known string to a know file in the bind mounted directory
# ./container-output-dir
# for test purposes -- test checks that the file was written.
def setup(command_context: DeployCommandContext, parameters, extra_args):
    host_directory = "./container-output-dir"
    host_directory_absolute = Path(extra_args[0]).absolute().joinpath(host_directory)
    host_directory_absolute.mkdir(parents=True, exist_ok=True)
    mounts = [VolumeMapping(str(host_directory_absolute), "/data")]
    output, status = run_container_command(
        command_context,
        "test",
        "echo output-data > /data/output-file && echo success",
        mounts,
    )


def init(command_context: DeployCommandContext):
    yaml = get_yaml()
    return yaml.load(default_spec_file_content)


def create(deployment_context: DeploymentContext, extra_args):
    data = "create-command-output-data"
    output_file_path = deployment_context.deployment_dir.joinpath("create-file")
    with open(output_file_path, "w+") as output_file:
        output_file.write(data)


def get_state(command_context: DeployCommandContext):
    print("Here we get state")
    return State.CONFIGURED


def change_state(command_context: DeployCommandContext):
    pass
