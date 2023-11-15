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
from stack_orchestrator.deploy.deployer_factory import getDeployer


@click.command()
@click.option("--image", help="image to deploy", required=True)
@click.option("--deploy-to", default="compose", help="deployment type ([Docker] 'compose' or 'k8s')")
@click.option("--env-file", help="environment file for webapp")
@click.pass_context
def command(ctx, image, deploy_to, env_file):
    '''build the specified webapp container'''

    env = {}
    if env_file:
        env = dotenv_values(env_file)

    unique_cluster_descriptor = f"{image},{env}"
    hash = hashlib.md5(unique_cluster_descriptor.encode()).hexdigest()
    cluster = f"laconic-webapp-{hash}"

    deployer = getDeployer(deploy_to,
                           deployment_dir=None,
                           compose_files=None,
                           compose_project_name=cluster,
                           compose_env_file=None)

    container = deployer.run(image, command=[], user=None, volumes=[], entrypoint=None, env=env, detach=True)

    # Make configurable?
    webappPort = "3000/tcp"
    # TODO: This assumes a Docker container object...
    if webappPort in container.network_settings.ports:
        mapping = container.network_settings.ports[webappPort][0]
        print(f"""Image: {image}\nID: {container.id}\nURL: http://localhost:{mapping['HostPort']}""")
