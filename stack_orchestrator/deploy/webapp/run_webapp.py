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

# Builds webapp containers

# env vars:
# CERC_REPO_BASE_DIR defaults to ~/cerc

# TODO: display the available list of containers; allow re-build of either all or specific containers

import hashlib
import click
from dotenv import dotenv_values

from stack_orchestrator import constants
from stack_orchestrator.deploy.deployer_factory import getDeployer

WEBAPP_PORT = 3000

@click.command()
@click.option("--image", help="image to deploy", required=True)
@click.option("--env-file", help="environment file for webapp")
@click.option("--port", help="port to use (default random)")
@click.pass_context
def command(ctx, image, env_file, port):
    '''run the specified webapp container'''

    env = {}
    if env_file:
        env = dotenv_values(env_file)

    unique_cluster_descriptor = f"{image},{env}"
    hash = hashlib.md5(unique_cluster_descriptor.encode()).hexdigest()
    cluster = f"laconic-webapp-{hash}"

    deployer = getDeployer(type=constants.compose_deploy_type,
                           deployment_context=None,
                           compose_files=None,
                           compose_project_name=cluster,
                           compose_env_file=None)

    ports = []
    if port:
        ports = [(port, WEBAPP_PORT)]
    container = deployer.run(image, command=[], user=None, volumes=[], entrypoint=None, env=env, ports=ports, detach=True)

    # Make configurable?
    webappPort = f"{WEBAPP_PORT}/tcp"
    # TODO: This assumes a Docker container object...
    if webappPort in container.network_settings.ports:
        mapping = container.network_settings.ports[webappPort][0]
        print(f"""Image: {image}\nID: {container.id}\nURL: http://localhost:{mapping['HostPort']}""")
