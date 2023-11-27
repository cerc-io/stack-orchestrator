# Copyright ©2023 Vulcanize

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

import click
from pathlib import Path

from stack_orchestrator.util import error_exit, global_options2
from stack_orchestrator.deploy.deployment_create import init_operation, create_operation
from stack_orchestrator.deploy.deploy import create_deploy_context
from stack_orchestrator.deploy.deploy_types import DeployCommandContext


def _fixup_container_tag(deployment_dir: str, image: str):
    deployment_dir_path = Path(deployment_dir)
    compose_file = deployment_dir_path.joinpath("compose", "docker-compose-webapp-template.yml")
    # replace "cerc/webapp-container:local" in the file with our image tag
    with open(compose_file) as rfile:
        contents = rfile.read()
        contents = contents.replace("cerc/webapp-container:local", image)
    with open(compose_file, "w") as wfile:
        wfile.write(contents)


@click.group()
@click.pass_context
def command(ctx):
    '''manage a webapp deployment'''

    # Check that --stack wasn't supplied
    if ctx.parent.obj.stack:
        error_exit("--stack can't be supplied with the deploy-webapp command")


@command.command()
@click.option("--kube-config", help="Provide a config file for a k8s deployment")
@click.option("--image-registry", help="Provide a container image registry url for this k8s cluster")
@click.option("--deployment-dir", help="Create deployment files in this directory", required=True)
@click.option("--image", help="image to deploy", required=True)
@click.option("--env-file", help="environment file for webapp")
@click.pass_context
def create(ctx, deployment_dir, image, kube_config, image_registry, env_file):
    '''create a deployment for the specified webapp container'''
    # Do the equivalent of:
    # 1. laconic-so --stack webapp-template deploy --deploy-to k8s init --output webapp-spec.yml
    #   --config (eqivalent of the contents of my-config.env)
    # 2. laconic-so  --stack webapp-template deploy --deploy-to k8s create --deployment-dir test-deployment
    #   --spec-file webapp-spec.yml
    # 3. Replace the container image tag with the specified image
    deployment_dir_path = Path(deployment_dir)
    # Check the deployment dir does not exist
    if deployment_dir_path.exists():
        error_exit(f"Deployment dir {deployment_dir} already exists")
    # Generate a temporary file name for the spec file
    spec_file_name = "webapp-spec.yml"
    # Specify the webapp template stack
    stack = "webapp-template"
    # TODO: support env file
    deploy_command_context: DeployCommandContext = create_deploy_context(
        global_options2(ctx), None, stack, None, None, None, env_file, "k8s"
        )
    init_operation(
        deploy_command_context,
        stack,
        "k8s",
        None,
        kube_config,
        image_registry,
        spec_file_name,
        None
    )
    create_operation(
        deploy_command_context,
        spec_file_name,
        deployment_dir,
        None,
        None
    )
    # Fix up the container tag inside the deployment compose file
    _fixup_container_tag(deployment_dir, image)
