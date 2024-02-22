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

from stack_orchestrator.deploy.deployment_context import DeploymentContext
from ruamel.yaml import YAML


def create(context: DeploymentContext, extra_args):
    fixturenet_eth_compose_file = context.deployment_dir.joinpath('compose', 'docker-compose-fixturenet-eth.yml')

    with open(fixturenet_eth_compose_file, 'r') as yaml_file:
        yaml = YAML()
        yaml_data = yaml.load(yaml_file)

    new_script = '../config/fixturenet-optimism/run-geth.sh:/opt/testnet/run.sh'
    if new_script not in yaml_data['services']['fixturenet-eth-geth-1']['volumes']:
        yaml_data['services']['fixturenet-eth-geth-1']['volumes'].append(new_script)

    with open(fixturenet_eth_compose_file, 'w') as yaml_file:
        yaml = YAML()
        yaml.dump(yaml_data, yaml_file)

    # load fixturenet-optimism compose file
    fixturenet_optimism_compose_file = context.deployment_dir.joinpath(
        "compose",
        "docker-compose-fixturenet-optimism.yml"
    )

    with open(fixturenet_optimism_compose_file, 'r') as yaml_file:
        yaml = YAML()
        yaml_data = yaml.load(yaml_file)

    # mount the funding script to volumes
    fund_accounts_script = (
        '../config/watcher-mobymask-v3-demo/local/fund-accounts-on-l2.sh'
        ':/app/packages/contracts-bedrock/fund-accounts-on-l2.sh'
    )
    yaml_data['services']['fixturenet-optimism-contracts']['volumes'].append(fund_accounts_script)

    # update command to run the script
    yaml_data['services']['fixturenet-optimism-contracts']['command'] = (
        '"./wait-for-it.sh -h ${CERC_L1_HOST:-$${DEFAULT_CERC_L1_HOST}}'
        ' -p ${CERC_L1_PORT:-$${DEFAULT_CERC_L1_PORT}} -s -t 60'
        ' -- ./deploy-contracts.sh && ./fund-accounts-on-l2.sh"'
    )

    # update port mapping for op-geth: 0.0.0.0:8545:8545
    existing_ports = yaml_data['services']['op-geth']['ports']
    new_ports = ["0.0.0.0:8545:8545" if "8545" in s else s for s in existing_ports]
    yaml_data['services']['op-geth']['ports'] = new_ports

    with open(fixturenet_optimism_compose_file, 'w') as yaml_file:
        yaml = YAML()
        yaml.dump(yaml_data, yaml_file)

    return None
