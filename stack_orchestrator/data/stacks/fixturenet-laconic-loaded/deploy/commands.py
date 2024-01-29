# Copyright © 2022-2024 Vulcanize

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

from stack_orchestrator.util import get_yaml, get_config_file_dir
from stack_orchestrator.deploy.deploy_types import DeployCommandContext
from stack_orchestrator.deploy.deployment_context import DeploymentContext
from pathlib import Path
from shutil import copy

default_spec_file_content = ""


def _stack_config_dir(context: DeploymentContext) -> Path:
    return get_config_file_dir().joinpath(context.stack.name)

def _deployment_volume_dir(context: DeploymentContext, volume_name: str) -> Path:
    return context.deployment_dir.joinpath("data", volume_name)


def _copy_laconicd_scripts(context: DeploymentContext):
    scripts = [
        "create-fixturenet.sh",
        "export-mykey.sh",
        "export-myaddress.sh"
    ]
    destination_dir = _deployment_volume_dir(context, "laconicd-scripts")
    for script in scripts:
        # ../config/fixturenet-laconicd/
        source_file = _stack_config_dir(context).joinpath(script)
        copy(source_file, destination_dir)


def _copy_cli_template(context: DeploymentContext):
    destination_dir = _deployment_volume_dir(context, "cli-config")
    # ../config/fixturenet-laconicd/
    source_file = _stack_config_dir(context).joinpath("registry-cli-config-template.yml")
    copy(source_file, destination_dir)


def setup(command_context: DeployCommandContext, parameters, extra_args):
    pass


def init(command_context: DeployCommandContext):
    yaml = get_yaml()
    return yaml.load(default_spec_file_content)


def create(context: DeploymentContext, extra_args):
    _copy_laconicd_scripts(context)
    _copy_cli_template(context)


def get_state(command_context: DeployCommandContext):
    pass


def change_state(command_context: DeployCommandContext):
    pass
