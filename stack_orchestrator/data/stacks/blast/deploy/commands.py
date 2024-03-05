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


from pathlib import Path
from shutil import copy


def create(context, extra_args):
    # Our goal here is just to copy the genesis.json file for blast
    deployment_config_dir = context.deployment_dir.joinpath("data", "blast-data")
    command_context = extra_args[2]
    compose_file = [f for f in command_context.cluster_context.compose_files if "blast" in f][0]
    source_config_file = Path(compose_file).parent.parent.joinpath("config", "blast", "genesis.json")
    copy(source_config_file, deployment_config_dir)
