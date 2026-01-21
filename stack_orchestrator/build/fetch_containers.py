# Copyright © 2024 Vulcanize

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
from dataclasses import dataclass
import json
import platform
from python_on_whales import DockerClient
from python_on_whales.components.manifest.cli_wrapper import ManifestCLI, ManifestList
from python_on_whales.utils import run
import requests
from typing import List

from stack_orchestrator.opts import opts
from stack_orchestrator.util import include_exclude_check, error_exit
from stack_orchestrator.build.build_util import get_containers_in_scope

# Experimental fetch-container command


@dataclass
class RegistryInfo:
    registry: str
    registry_username: str
    registry_token: str


# Extending this code to support the --verbose option, cnosider contributing upstream
# https://github.com/gabrieldemarmiesse/python-on-whales/blob/master/python_on_whales/components/manifest/cli_wrapper.py#L129
class ExtendedManifestCLI(ManifestCLI):
    def inspect_verbose(self, x: str) -> ManifestList:
        """Returns a Docker manifest list object."""
        json_str = run(self.docker_cmd + ["manifest", "inspect", "--verbose", x])
        return json.loads(json_str)


def _local_tag_for(container: str):
    return f"{container}:local"


# See: https://docker-docs.uclv.cu/registry/spec/api/
# Emulate this:
# $ curl -u "my-username:my-token" -X GET "https://<container-registry-hostname>/v2/cerc-io/cerc/test-container/tags/list"
# {"name":"cerc-io/cerc/test-container","tags":["202402232130","202402232208"]}
def _get_tags_for_container(container: str, registry_info: RegistryInfo) -> List[str]:
    # registry looks like: git.vdb.to/cerc-io
    registry_parts = registry_info.registry.split("/")
    url = f"https://{registry_parts[0]}/v2/{registry_parts[1]}/{container}/tags/list"
    if opts.o.debug:
        print(f"Fetching tags from: {url}")
    response = requests.get(url, auth=(registry_info.registry_username, registry_info.registry_token))
    if response.status_code == 200:
        tag_info = response.json()
        if opts.o.debug:
            print(f"container tags list: {tag_info}")
        tags_array = tag_info["tags"]
        return tags_array
    else:
        error_exit(f"failed to fetch tags from image registry, status code: {response.status_code}")


def _find_latest(candidate_tags: List[str]):
    # Lex sort should give us the latest first
    sorted_candidates = sorted(candidate_tags)
    if opts.o.debug:
        print(f"sorted candidates: {sorted_candidates}")
    return sorted_candidates[-1]


def _filter_for_platform(container: str,
                         registry_info: RegistryInfo,
                         tag_list: List[str]) -> List[str] :
    filtered_tags = []
    this_machine = platform.machine()
    # Translate between Python and docker platform names
    if this_machine == "x86_64":
        this_machine = "amd64"
    if this_machine == "aarch64":
        this_machine = "arm64"
    if opts.o.debug:
        print(f"Python says the architecture is: {this_machine}")
    docker = DockerClient()
    for tag in tag_list:
        remote_tag = f"{registry_info.registry}/{container}:{tag}"
        manifest_cmd = ExtendedManifestCLI(docker.client_config)
        manifest = manifest_cmd.inspect_verbose(remote_tag)
        if opts.o.debug:
            print(f"manifest: {manifest}")
        image_architecture =  manifest["Descriptor"]["platform"]["architecture"]
        if opts.o.debug:
            print(f"image_architecture: {image_architecture}")
        if this_machine == image_architecture:
            filtered_tags.append(tag)
    if opts.o.debug:
        print(f"Tags filtered for platform: {filtered_tags}")
    return filtered_tags


def _get_latest_image(container: str, registry_info: RegistryInfo):
    all_tags = _get_tags_for_container(container, registry_info)
    tags_for_platform = _filter_for_platform(container, registry_info, all_tags)
    if len(tags_for_platform) > 0:
        latest_tag = _find_latest(tags_for_platform)
        return f"{container}:{latest_tag}"
    else:
        return None


def _fetch_image(tag: str, registry_info: RegistryInfo):
    docker = DockerClient()
    remote_tag = f"{registry_info.registry}/{tag}"
    if opts.o.debug:
        print(f"Attempting to pull this image: {remote_tag}")
    docker.image.pull(remote_tag)


def _exists_locally(container: str):
    docker = DockerClient()
    return docker.image.exists(_local_tag_for(container))


def _add_local_tag(remote_tag: str, registry: str, local_tag: str):
    docker = DockerClient()
    docker.image.tag(f"{registry}/{remote_tag}", local_tag)


@click.command()
@click.option('--include', help="only fetch these containers")
@click.option('--exclude', help="don\'t fetch these containers")
@click.option("--force-local-overwrite", is_flag=True, default=False, help="Overwrite a locally built image, if present")
@click.option("--image-registry", required=True, help="Specify the image registry to fetch from")
@click.option("--registry-username", required=True, help="Specify the image registry username")
@click.option("--registry-token", required=True, help="Specify the image registry access token")
@click.pass_context
def command(ctx, include, exclude, force_local_overwrite, image_registry, registry_username, registry_token):
    '''EXPERIMENTAL: fetch the images for a stack from remote registry'''

    registry_info = RegistryInfo(image_registry, registry_username, registry_token)
    docker = DockerClient()
    if not opts.o.quiet:
        print("Logging into container registry:")
    docker.login(registry_info.registry, registry_info.registry_username, registry_info.registry_token)
    # Generate list of target containers
    stack = ctx.obj.stack
    containers_in_scope = get_containers_in_scope(stack)
    all_containers_found = True
    for container in containers_in_scope:
        local_tag = _local_tag_for(container)
        if include_exclude_check(container, include, exclude):
            if opts.o.debug:
                print(f"Processing: {container}")
            # For each container, attempt to find the latest of a set of
            # images with the correct name and platform in the specified registry
            image_to_fetch = _get_latest_image(container, registry_info)
            if not image_to_fetch:
                print(f"Warning: no image found to fetch for container: {container}")
                all_containers_found = False
                continue
            if opts.o.debug:
                print(f"Fetching: {image_to_fetch}")
            _fetch_image(image_to_fetch, registry_info)
            # Now check if the target container already exists exists locally already
            if (_exists_locally(container)):
                if not opts.o.quiet:
                    print(f"Container image {container} already exists locally")
                # if so, fail unless the user specified force-local-overwrite
                if (force_local_overwrite):
                    # In that case remove the existing :local tag
                    if not opts.o.quiet:
                        print(f"Warning: overwriting local tag from this image: {container} because "
                              "--force-local-overwrite was specified")
                else:
                    if not opts.o.quiet:
                        print(f"Skipping local tagging for this image: {container} because that would "
                              "overwrite an existing :local tagged image, use --force-local-overwrite to do so.")
                    continue
            # Tag the fetched image with the :local tag
            _add_local_tag(image_to_fetch, image_registry, local_tag)
        else:
            if opts.o.verbose:
                print(f"Excluding: {container}")
    if not all_containers_found:
        print("Warning: couldn't find usable images for one or more containers, this stack will not deploy")
