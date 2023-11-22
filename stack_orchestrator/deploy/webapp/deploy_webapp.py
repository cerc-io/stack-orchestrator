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

from stack_orchestrator.util import error_exit


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
