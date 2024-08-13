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
from stack_orchestrator.deploy.deploy_types import DeployCommandContext, LaconicStackSetupCommand
from stack_orchestrator.deploy.deployment_context import DeploymentContext
from stack_orchestrator.deploy.stack_state import State
from stack_orchestrator.deploy.deploy_util import VolumeMapping, run_container_command
from stack_orchestrator.opts import opts
from enum import Enum
from pathlib import Path
from shutil import copyfile, copytree
import os
import sys
import tomli
import re

default_spec_file_content = ""


class SetupPhase(Enum):
    INITIALIZE = 1
    JOIN = 2
    CONNECT = 3
    CREATE = 4
    ILLEGAL = 5


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


def _comma_delimited_to_list(list_str: str):
    return list_str.split(",") if list_str else []


def _get_node_keys_from_gentx_files(gentx_address_list: str):
    gentx_addresses = _comma_delimited_to_list(gentx_address_list)
    return gentx_addresses


def _copy_gentx_files(network_dir: Path, gentx_file_list: str):
    gentx_files = _comma_delimited_to_list(gentx_file_list)
    for gentx_file in gentx_files:
        gentx_file_path = Path(gentx_file)
        copyfile(gentx_file_path, os.path.join(network_dir, "config", "gentx", os.path.basename(gentx_file_path)))


def _remove_persistent_peers(network_dir: Path):
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


def _insert_persistent_peers(config_dir: Path, new_persistent_peers: str):
    config_file_path = config_dir.joinpath("config.toml")
    if not config_file_path.exists():
        print("Error: config.toml not found")
        sys.exit(1)
    with open(config_file_path, "r") as input_file:
        config_file_content = input_file.read()
        persistent_peers_pattern = r'^persistent_peers = ""'
        replace_with = f"persistent_peers = \"{new_persistent_peers}\""
        config_file_content = re.sub(persistent_peers_pattern, replace_with, config_file_content, flags=re.MULTILINE)
    with open(config_file_path, "w") as output_file:
        output_file.write(config_file_content)


def _enable_cors(config_dir: Path):
    config_file_path = config_dir.joinpath("config.toml")
    if not config_file_path.exists():
        print("Error: config.toml not found")
        sys.exit(1)
    with open(config_file_path, "r") as input_file:
        config_file_content = input_file.read()
        cors_pattern = r'^cors_allowed_origins = \[]'
        replace_with = 'cors_allowed_origins = ["*"]'
        config_file_content = re.sub(cors_pattern, replace_with, config_file_content, flags=re.MULTILINE)
    with open(config_file_path, "w") as output_file:
        output_file.write(config_file_content)
    app_file_path = config_dir.joinpath("app.toml")
    if not app_file_path.exists():
        print("Error: app.toml not found")
        sys.exit(1)
    with open(app_file_path, "r") as input_file:
        app_file_content = input_file.read()
        cors_pattern = r'^enabled-unsafe-cors = false'
        replace_with = "enabled-unsafe-cors = true"
        app_file_content = re.sub(cors_pattern, replace_with, app_file_content, flags=re.MULTILINE)
    with open(app_file_path, "w") as output_file:
        output_file.write(app_file_content)


def _set_listen_address(config_dir: Path):
    config_file_path = config_dir.joinpath("config.toml")
    if not config_file_path.exists():
        print("Error: config.toml not found")
        sys.exit(1)
    with open(config_file_path, "r") as input_file:
        config_file_content = input_file.read()
        existing_pattern = r'^laddr = "tcp://127.0.0.1:26657"'
        replace_with = 'laddr = "tcp://0.0.0.0:26657"'
        print(f"Replacing in: {config_file_path}")
        config_file_content = re.sub(existing_pattern, replace_with, config_file_content, flags=re.MULTILINE)
    with open(config_file_path, "w") as output_file:
        output_file.write(config_file_content)
    app_file_path = config_dir.joinpath("app.toml")
    if not app_file_path.exists():
        print("Error: app.toml not found")
        sys.exit(1)
    with open(app_file_path, "r") as input_file:
        app_file_content = input_file.read()
        existing_pattern1 = r'^address = "tcp://localhost:1317"'
        replace_with1 = 'address = "tcp://0.0.0.0:1317"'
        app_file_content = re.sub(existing_pattern1, replace_with1, app_file_content, flags=re.MULTILINE)
        existing_pattern2 = r'^address = "localhost:9090"'
        replace_with2 = 'address = "0.0.0.0:9090"'
        app_file_content = re.sub(existing_pattern2, replace_with2, app_file_content, flags=re.MULTILINE)
    with open(app_file_path, "w") as output_file:
        output_file.write(app_file_content)


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
    elif parameters.connect_network:
        if parameters.initialize_network or parameters.join_network:
            print("Can't supply --initialize-network or --join-network with --connect-network")
            sys.exit(1)
        phase = SetupPhase.CONNECT
    return phase


def setup(command_context: DeployCommandContext, parameters: LaconicStackSetupCommand, extra_args):

    options = opts.o

    currency = "alnt"  # Does this need to be a parameter?

    if options.debug:
        print(f"parameters: {parameters}")

    phase = _phase_from_params(parameters)

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
                --chain-id {parameters.chain_id} --default-denom {currency}", mounts)
        if options.debug:
            print(f"Command output: {output}")

    elif phase == SetupPhase.JOIN:
        # In the join phase (alternative to connect) we are participating in a genesis ceremony for the chain
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
            f"laconicd genesis add-genesis-account {parameters.key_name} 12900000000000000000000{currency}\
                --home {laconicd_home_path_in_container} --keyring-backend test",
            mounts)
        if options.debug:
            print(f"Command output: {output2}")
        output3, status3 = run_container_command(
            command_context,
            "laconicd",
            f"laconicd genesis gentx  {parameters.key_name} 90000000000{currency} --home {laconicd_home_path_in_container}\
                --chain-id {chain_id} --keyring-backend test",
            mounts)
        if options.debug:
            print(f"Command output: {output3}")
        output4, status4 = run_container_command(
            command_context,
            "laconicd",
            f"laconicd keys show  {parameters.key_name} -a --home {laconicd_home_path_in_container} --keyring-backend test",
            mounts)
        print(f"Node account address: {output4}")

    elif phase == SetupPhase.CONNECT:
        # In the connect phase (named to not conflict with join) we are making a node that syncs a chain with existing genesis.json
        # but not with validator role. We need this kind of node in order to bootstrap it into a validator after it syncs
        output1, status1 = run_container_command(
            command_context, "laconicd", f"laconicd keys add {parameters.key_name} --home {laconicd_home_path_in_container}\
                --keyring-backend test", mounts)
        if options.debug:
            print(f"Command output: {output1}")
        output2, status2 = run_container_command(
            command_context,
            "laconicd",
            f"laconicd keys show  {parameters.key_name} -a --home {laconicd_home_path_in_container} --keyring-backend test",
            mounts)
        print(f"Node account address: {output2}")
        output3, status3 = run_container_command(
            command_context,
            "laconicd",
            f"laconicd cometbft show-validator --home {laconicd_home_path_in_container}",
            mounts)
        print(f"Node validator address: {output3}")

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
            # First look in the supplied gentx files for the other nodes' keys
            other_node_keys = _get_node_keys_from_gentx_files(parameters.gentx_address_list)
            # Add those keys to our genesis, with balances we determine here (why?)
            for other_node_key in other_node_keys:
                outputk, statusk = run_container_command(
                    command_context, "laconicd", f"laconicd genesis add-genesis-account {other_node_key} \
                        12900000000000000000000{currency}\
                        --home {laconicd_home_path_in_container} --keyring-backend test", mounts)
            if options.debug:
                print(f"Command output: {outputk}")
            # Copy the gentx json files into our network dir
            _copy_gentx_files(network_dir, parameters.gentx_file_list)
            # Now we can run collect-gentxs
            output1, status1 = run_container_command(
                command_context, "laconicd", f"laconicd genesis collect-gentxs --home {laconicd_home_path_in_container}", mounts)
            if options.debug:
                print(f"Command output: {output1}")
            print(f"Generated genesis file, please copy to other nodes as required: \
                {os.path.join(network_dir, 'config', 'genesis.json')}")
            # Last thing, collect-gentxs puts a likely bogus set of persistent_peers in config.toml so we remove that now
            _remove_persistent_peers(network_dir)
        # In both cases we validate the genesis file now
        output2, status1 = run_container_command(
            command_context, "laconicd", f"laconicd genesis validate-genesis --home {laconicd_home_path_in_container}", mounts)
        print(f"validate-genesis result: {output2}")

    else:
        print("Illegal parameters supplied")
        sys.exit(1)


def create(deployment_context: DeploymentContext, extra_args):
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
    deployment_config_dir = deployment_context.deployment_dir.joinpath("data", "laconicd-config")
    copytree(config_dir_path, deployment_config_dir, dirs_exist_ok=True)
    # If supplied, add the initial persistent peers to the config file
    if extra_args[1]:
        initial_persistent_peers = extra_args[1]
        _insert_persistent_peers(deployment_config_dir, initial_persistent_peers)
    # Enable CORS headers so explorers and so on can talk to the node
    _enable_cors(deployment_config_dir)
    _set_listen_address(deployment_config_dir)
    # Copy the data directory contents into our deployment
    # TODO: change this to work with non local paths
    deployment_data_dir = deployment_context.deployment_dir.joinpath("data", "laconicd-data")
    copytree(data_dir_path, deployment_data_dir, dirs_exist_ok=True)


def init(command_context: DeployCommandContext):
    yaml = get_yaml()
    return yaml.load(default_spec_file_content)


def get_state(command_context: DeployCommandContext):
    return State.CONFIGURED


def change_state(command_context: DeployCommandContext):
    pass
