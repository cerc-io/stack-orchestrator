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

from app.util import get_yaml
from app.deploy_types import DeployCommandContext, LaconicStackSetupCommand
from app.stack_state import State
from app.deploy_util import VolumeMapping, run_container_command
from enum import Enum
from pathlib import Path
import os
import sys
import tomli

default_spec_file_content = """config:
    node_moniker: my-node-name
    chain_id: my-chain-id
"""

init_help_text = """Add helpful text here on setting config variables.
"""


class SetupPhase(Enum):
    INITIALIZE = 1
    JOIN = 2
    CREATE = 3
    ILLEGAL = 3


def _get_chain_id_from_config():
    chain_id = None
    with open("laconic-network-dir/config/client.toml", "rb") as f:
        toml_dict = tomli.load(f)
        chain_id = toml_dict["chain_id"]
    return chain_id


def _get_node_moniker_from_config():
    moniker = None
    with open("laconic-network-dir/config/config.toml", "rb") as f:
        toml_dict = tomli.load(f)
        moniker = toml_dict["moniker"]
    return moniker


def setup(command_context: DeployCommandContext, parameters: LaconicStackSetupCommand, extra_args):

    print(f"parameters: {parameters}")

    phase = SetupPhase.ILLEGAL

    if parameters.initialize_network:
        if parameters.join_network or parameters.create_network:
            print("Can't supply --join-network or --create-network with --initialize-network")
            sys.exit(1)
        if not parameters.chain_id:
            print("--chain-id is required")
            sys.exit(1)
        # node_moniker must be supplied
        if not parameters.node_moniker:
            print("Error: --node-moniker is required")
            sys.exit(1)
        phase = SetupPhase.INITIALIZE
    elif parameters.join_network:
        if parameters.initialize_network or parameters.create_network:
            print("Can't supply --initialize-network or --create-network with --join-network")
            sys.exit(1)
        phase = SetupPhase.JOIN
    elif parameters.create_network:
        if parameters.initialize_network or parameters.join_network:
            print("Can't supply --initialize-network or --join-network with --create-network")
            sys.exit(1)
        phase = SetupPhase.CREATE

    network_dir = Path(parameters.network_dir).absolute()
    laconicd_home_path_in_container = "/laconicd-home"
    mounts = [
        VolumeMapping(network_dir, laconicd_home_path_in_container)
    ]

    if phase == SetupPhase.INITIALIZE:

        # We want to create the directory so if it exists that's an error
        if os.path.exists(network_dir):
            print(f"Error: network directory {network_dir} already exists")
            sys.exit(1)

        os.mkdir(network_dir)

        output, status = run_container_command(
            command_context,
            "laconicd", f"laconicd init {parameters.node_moniker} --home {laconicd_home_path_in_container} --chain-id {parameters.chain_id}", mounts)
        print(f"Command output: {output}")

    elif phase == SetupPhase.JOIN:
        # We want to create the directory so if it exists that's an error
        if not os.path.exists(network_dir):
            print(f"Error: network directory {network_dir} doesn't exist")
            sys.exit(1)
        # Get the chain_id from the config file created in the INITIALIZE phase
        chain_id = _get_chain_id_from_config()

        output1, status1 = run_container_command(
            command_context, "laconicd", f"laconicd keys add {parameters.key_name} --home {laconicd_home_path_in_container} --keyring-backend test", mounts)
        print(f"Command output: {output1}")
        output2, status2 = run_container_command(
            command_context, 
            "laconicd",
            f"laconicd add-genesis-account {parameters.key_name} 12900000000000000000000achk --home {laconicd_home_path_in_container} --keyring-backend test",
            mounts)
        print(f"Command output: {output2}")        
        output3, status3 = run_container_command(
            command_context, 
            "laconicd",
            f"laconicd gentx  {parameters.key_name} 90000000000achk --home {laconicd_home_path_in_container} --chain-id {chain_id} --keyring-backend test",
            mounts)
        print(f"Command output: {output3}")

    elif phase == SetupPhase.CREATE:
        # We want to create the directory so if it exists that's an error
        if not os.path.exists(network_dir):
            print(f"Error: network directory {network_dir} doesn't exist")
            sys.exit(1)

        output1, status1 = run_container_command(
            command_context, "laconicd", f"laconicd collect-gentxs --home {laconicd_home_path_in_container}", mounts)
        print(f"Command output: {output1}")        
        output2, status1 = run_container_command(
            command_context, "laconicd", f"laconicd validate-genesis --home {laconicd_home_path_in_container}", mounts)
        print(f"Command output: {output2}")
    else:
        print("Illegal parameters supplied")
        sys.exit(1)


def create(command_context: DeployCommandContext):
    print("Copy the network files here")


def init(command_context: DeployCommandContext):
    print(init_help_text)
    yaml = get_yaml()
    return yaml.load(default_spec_file_content)


def get_state(command_context: DeployCommandContext):
    print("Here we get state")
    return State.CONFIGURED


def change_state(command_context: DeployCommandContext):
    pass
