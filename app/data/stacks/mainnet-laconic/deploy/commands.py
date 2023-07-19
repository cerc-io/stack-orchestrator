# Copyright © 2022, 2023 Cerc

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

from dataclasses import dataclass
from app.util import get_yaml
from app.stack_state import State

default_spec_file_content = """config:
    node_moniker: my-node-name
    chain_id: my-chain-id
"""

init_help_text = """Add helpful text here on setting config variables.
"""

@dataclass
class VolumeMapping:
    host_path: str
    container_path: str


# In order to make this, we need the ability to run the stack
# In theory we can make this same way as we would run deploy up
def run_container_command(ctx, ontainer, command, mounts):
    deploy_context = ctx.obj
    pass


def setup(ctx):
    node_moniker = "dbdb-node"
    chain_id = "laconic_81337-1"
    mounts = [
        VolumeMapping("./path", "~/.laconicd")
    ]
    output, status = run_container_command(ctx, "laconicd", f"laconicd init {node_moniker} --chain-id {chain_id}", mounts)


def init(command_context):
    print(init_help_text)
    yaml = get_yaml()
    return yaml.load(default_spec_file_content)


def get_state(command_context):
    print("Here we get state")
    return State.CONFIGURED


def change_state(command_context):
    pass
