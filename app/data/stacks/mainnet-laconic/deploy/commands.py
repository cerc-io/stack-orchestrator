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
from app.deploy_types import DeployCommandContext, LaconicStackSetupCommand, DeploymentContext
from app.stack_state import State
from app.deploy_util import VolumeMapping, run_container_command
from app.command_types import CommandOptions
from enum import Enum
from pathlib import Path
from shutil import copyfile, copytree
import json
import os
import sys
import tomli
import re

default_spec_file_content = """config:
    node_moniker: my-node-name
    chain_id: my-chain-id
"""


class SetupPhase(Enum):
    INITIALIZE = 1
    JOIN = 2
    CREATE = 3
    ILLEGAL = 3


def _client_toml_path(network_dir: Path):
    return network_dir.joinpath("config", "client.toml")


def _config_toml_path(network_dir: Path):
    return network_dir.joinpath("config", "config.toml")


def _get_chain_id_from_config(network_dir: Path):
    chain_id = None
    with open(_client_toml_path(network_dir), "rb") as f:
        toml_dict = tomli.load(f)
        chain_id = toml_dict["chain-id"]
    return chain_id


def _get_node_moniker_from_config(network_dir: Path):
    moniker = None
    with open(_client_toml_path(network_dir), "rb") as f:
        toml_dict = tomli.load(f)
        moniker = toml_dict["moniker"]
    return moniker


def _get_node_key_from_gentx(options: CommandOptions, gentx_file_name: str):
    gentx_file_path = Path(gentx_file_name)
    if gentx_file_path.exists():
        with open(Path(gentx_file_name), "rb") as f:
            parsed_json = json.load(f)
            return parsed_json['body']['messages'][0]['delegator_address']
    else:
        print(f"Error: gentx file: {gentx_file_name} does not exist")
        sys.exit(1)


def _comma_delimited_to_list(list_str: str):
    return list_str.split(",") if list_str else []


def _get_node_keys_from_gentx_files(options: CommandOptions, gentx_file_list: str):
    node_keys = []
    gentx_files = _comma_delimited_to_list(gentx_file_list)
    for gentx_file in gentx_files:
        node_key = _get_node_key_from_gentx(options, gentx_file)
        if node_key:
            node_keys.append(node_key)
    return node_keys


def _copy_gentx_files(options: CommandOptions, network_dir: Path, gentx_file_list: str):
    gentx_files = _comma_delimited_to_list(gentx_file_list)
    for gentx_file in gentx_files:
        gentx_file_path = Path(gentx_file)
        copyfile(gentx_file_path, os.path.join(network_dir, "config", "gentx", os.path.basename(gentx_file_path)))


def _remove_persistent_peers(options: CommandOptions, network_dir: Path):
    config_file_path = _config_toml_path(network_dir)
    if not config_file_path.exists():
        print("Error: config.toml not found")
        sys.exit(1)
    with open(config_file_path, "r") as input_file:
        config_file_content = input_file.read()
        persistent_peers_pattern = '^persistent_peers = "(.+?)"'
        replace_with = "persistent_peers = \"\""
        config_file_content = re.sub(persistent_peers_pattern, replace_with, config_file_content, flags=re.MULTILINE)
    with open(config_file_path, "w") as output_file:
        output_file.write(config_file_content)


def _insert_persistent_peers(options: CommandOptions, config_dir: Path, new_persistent_peers: str):
    config_file_path = config_dir.joinpath("config.toml")
    if not config_file_path.exists():
        print("Error: config.toml not found")
        sys.exit(1)
    with open(config_file_path, "r") as input_file:
        config_file_content = input_file.read()
        persistent_peers_pattern = '^persistent_peers = ""'
        replace_with = f"persistent_peers = \"{new_persistent_peers}\""
        config_file_content = re.sub(persistent_peers_pattern, replace_with, config_file_content, flags=re.MULTILINE)
    with open(config_file_path, "w") as output_file:
        output_file.write(config_file_content)


def _phase_from_params(parameters):
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
    return phase


def setup(command_context: DeployCommandContext, parameters: LaconicStackSetupCommand, extra_args):

    options = command_context.cluster_context.options

    currency = "stake"  # Does this need to be a parameter?

    if options.debug:
        print(f"parameters: {parameters}")

    phase = _phase_from_params()

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
            "laconicd", f"laconicd init {parameters.node_moniker} --home {laconicd_home_path_in_container}\
                --chain-id {parameters.chain_id}", mounts)
        if options.debug:
            print(f"Command output: {output}")

    elif phase == SetupPhase.JOIN:
        if not os.path.exists(network_dir):
            print(f"Error: network directory {network_dir} doesn't exist")
            sys.exit(1)
        # Get the chain_id from the config file created in the INITIALIZE phase
        chain_id = _get_chain_id_from_config(network_dir)

        output1, status1 = run_container_command(
            command_context, "laconicd", f"laconicd keys add {parameters.key_name} --home {laconicd_home_path_in_container}\
                --keyring-backend test", mounts)
        if options.debug:
            print(f"Command output: {output1}")
        output2, status2 = run_container_command(
            command_context,
            "laconicd",
            f"laconicd add-genesis-account {parameters.key_name} 12900000000000000000000{currency}\
                --home {laconicd_home_path_in_container} --keyring-backend test",
            mounts)
        if options.debug:
            print(f"Command output: {output2}")
        output3, status3 = run_container_command(
            command_context,
            "laconicd",
            f"laconicd gentx  {parameters.key_name} 90000000000{currency} --home {laconicd_home_path_in_container}\
                --chain-id {chain_id} --keyring-backend test",
            mounts)
        if options.debug:
            print(f"Command output: {output3}")
        output4, status4 = run_container_command(
            command_context,
            "laconicd",
            f"laconicd keys show  {parameters.key_name} -a --home {laconicd_home_path_in_container} --keyring-backend test",
            mounts)
        print(f"Node validator address: {output4}")

    elif phase == SetupPhase.CREATE:
        if not os.path.exists(network_dir):
            print(f"Error: network directory {network_dir} doesn't exist")
            sys.exit(1)

        # In the CREATE phase, we are either a "coordinator" node, generating the genesis.json file ourselves
        # OR we are a "not-coordinator" node, consuming a genesis file we got from the coordinator node.
        if parameters.genesis_file:
            # We got the genesis file from elsewhere
            # Copy it into our network dir
            genesis_file_path = Path(parameters.genesis_file)
            if not os.path.exists(genesis_file_path):
                print(f"Error: supplied genesis file: {parameters.genesis_file} does not exist.")
                sys.exit(1)
            copyfile(genesis_file_path, os.path.join(network_dir, "config", os.path.basename(genesis_file_path)))
        else:
            # We're generating the genesis file
            if not parameters.gentx_file_list:
                print("Error: --gentx-files must be supplied")
                sys.exit(1)
            # First look in the supplied gentx files for the other nodes' keys
            other_node_keys = _get_node_keys_from_gentx_files(options, parameters.gentx_file_list)
            # Add those keys to our genesis, with balances we determine here (why?)
            for other_node_key in other_node_keys:
                outputk, statusk = run_container_command(
                    command_context, "laconicd", f"laconicd add-genesis-account {other_node_key} 12900000000000000000000{currency}\
                        --home {laconicd_home_path_in_container} --keyring-backend test", mounts)
            if options.debug:
                print(f"Command output: {outputk}")
            # Copy the gentx json files into our network dir
            _copy_gentx_files(options, network_dir, parameters.gentx_file_list)
            # Now we can run collect-gentxs
            output1, status1 = run_container_command(
                command_context, "laconicd", f"laconicd collect-gentxs --home {laconicd_home_path_in_container}", mounts)
            if options.debug:
                print(f"Command output: {output1}")
            print(f"Generated genesis file, please copy to other nodes as required: \
                {os.path.join(network_dir, 'config', 'genesis.json')}")
            # Last thing, collect-gentxs puts a likely bogus set of persistent_peers in config.toml so we remove that now
            _remove_persistent_peers(options, network_dir)
        # In both cases we validate the genesis file now
        output2, status1 = run_container_command(
            command_context, "laconicd", f"laconicd validate-genesis --home {laconicd_home_path_in_container}", mounts)
        print(f"validate-genesis result: {output2}")

    else:
        print("Illegal parameters supplied")
        sys.exit(1)


def create(context: DeploymentContext, extra_args):
    network_dir = extra_args[0]
    if network_dir is None:
        print("Error: --network-dir must be supplied")
        sys.exit(1)
    network_dir_path = Path(network_dir)
    if not (network_dir_path.exists() and network_dir_path.is_dir()):
        print(f"Error: supplied network directory does not exist: {network_dir}")
        sys.exit(1)
    config_dir_path = network_dir_path.joinpath("config")
    if not (config_dir_path.exists() and config_dir_path.is_dir()):
        print(f"Error: supplied network directory does not contain a config directory: {config_dir_path}")
        sys.exit(1)
    data_dir_path = network_dir_path.joinpath("data")
    if not (data_dir_path.exists() and data_dir_path.is_dir()):
        print(f"Error: supplied network directory does not contain a data directory: {data_dir_path}")
        sys.exit(1)
    # Copy the network directory contents into our deployment
    # TODO: change this to work with non local paths
    deployment_config_dir = context.deployment_dir.joinpath("data", "laconicd-config")
    copytree(config_dir_path, deployment_config_dir, dirs_exist_ok=True)
    # If supplied, add the initial persistent peers to the config file
    if extra_args[1]:
        initial_persistent_peers = extra_args[1]
        _insert_persistent_peers(context.command_context.cluster_context.options, deployment_config_dir, initial_persistent_peers)
    # Copy the data directory contents into our deployment
    # TODO: change this to work with non local paths
    deployment_data_dir = context.deployment_dir.joinpath("data", "laconicd-data")
    copytree(data_dir_path, deployment_data_dir, dirs_exist_ok=True)


def init(command_context: DeployCommandContext):
    yaml = get_yaml()
    return yaml.load(default_spec_file_content)


def get_state(command_context: DeployCommandContext):
    print("Here we get state")
    return State.CONFIGURED


def change_state(command_context: DeployCommandContext):
    pass
