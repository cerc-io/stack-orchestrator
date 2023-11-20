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

from typing import Set

from python_on_whales import DockerClient

from stack_orchestrator import constants
from stack_orchestrator.opts import opts
from stack_orchestrator.deploy.deployment_context import DeploymentContext
from stack_orchestrator.deploy.deploy_types import DeployCommandContext
from stack_orchestrator.deploy.deploy_util import images_for_deployment


def _image_needs_pushed(image: str):
    # TODO: this needs to be more intelligent
    return image.endswith(":local")


def _remote_tag_for_image(image: str, remote_repo_url: str):
    # Turns image tags of the form: foo/bar:local into remote.repo/org/bar:deploy
    (org, image_name_with_version) = image.split("/")
    (image_name, image_version) = image_name_with_version.split(":")
    return f"{remote_repo_url}/{image_name}:deploy"


# TODO: needs lots of error handling
def push_images_operation(command_context: DeployCommandContext, deployment_context: DeploymentContext):
    # Get the list of images for the stack
    cluster_context = command_context.cluster_context
    images: Set[str] = images_for_deployment(cluster_context.compose_files)
    # Tag the images for the remote repo
    remote_repo_url = deployment_context.spec.obj[constants.image_resigtry_key]
    docker = DockerClient()
    for image in images:
        if _image_needs_pushed(image):
            remote_tag = _remote_tag_for_image(image, remote_repo_url)
            if opts.o.verbose:
                print(f"Tagging {image} to {remote_tag}")
            docker.image.tag(image, remote_tag)
    # Run docker push commands to upload
    for image in images:
        if _image_needs_pushed(image):
            remote_tag = _remote_tag_for_image(image, remote_repo_url)
            if opts.o.verbose:
                print(f"Pushing image {remote_tag}")
            docker.image.push(remote_tag)
