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
from app.deploy.deploy_types import DeployCommandContext, LaconicStackSetupCommand, DeploymentContext
from ruamel.yaml import YAML

def create(context: DeploymentContext, extra_args):
    # Slightly modify the base fixturenet-eth compose file to replace the startup script for fixturenet-eth-geth-1
    # We need to start geth with the flag to allow non eip-155 compliant transactions in order to publish the
    # deterministic-deployment-proxy contract, which itself is a prereq for Optimism contract deployment
    fixturenet_eth_compose_file = context.deployment_dir.joinpath('compose', 'docker-compose-fixturenet-eth.yml')
    
    with open(fixturenet_eth_compose_file, 'r') as yaml_file:
        yaml=YAML()
        yaml_data = yaml.load(yaml_file)
    
    new_script = '../config/fixturenet-optimism/run-geth.sh:/opt/testnet/run.sh'

    if new_script not in yaml_data['services']['fixturenet-eth-geth-1']['volumes']:
        yaml_data['services']['fixturenet-eth-geth-1']['volumes'].append(new_script)
    
    with open(fixturenet_eth_compose_file, 'w') as yaml_file:
        yaml=YAML()
        yaml.dump(yaml_data, yaml_file)

    return None
