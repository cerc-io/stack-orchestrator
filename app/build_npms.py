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

# Builds or pulls containers for the system components

# env vars:
# CERC_REPO_BASE_DIR defaults to ~/cerc

import os
import sys
from shutil import rmtree, copytree
from decouple import config
import click
import importlib.resources
from python_on_whales import docker, DockerException
from .base import get_stack
from .util import include_exclude_check, get_parsed_stack_config

builder_js_image_name = "cerc/builder-js:local"

@click.command()
@click.option('--include', help="only build these packages")
@click.option('--exclude', help="don\'t build these packages")
@click.pass_context
def command(ctx, include, exclude):
    '''build the set of npm packages required for a complete stack'''

    quiet = ctx.obj.quiet
    verbose = ctx.obj.verbose
    dry_run = ctx.obj.dry_run
    local_stack = ctx.obj.local_stack
    debug = ctx.obj.debug
    stack = ctx.obj.stack
    continue_on_error = ctx.obj.continue_on_error

    _ensure_prerequisites()

    # build-npms depends on having access to a writable package registry
    # so we check here that it is available
    package_registry_stack = get_stack(ctx.obj, "package-registry")
    registry_available = package_registry_stack.ensure_available()
    if not registry_available:
        print("FATAL: no npm registry available for build-npms command")
        sys.exit(1)
    npm_registry_url = package_registry_stack.get_url()
    npm_registry_url_token = config("CERC_NPM_AUTH_TOKEN", default=None)
    if not npm_registry_url_token:
        print("FATAL: CERC_NPM_AUTH_TOKEN is not defined")
        sys.exit(1)

    if local_stack:
        dev_root_path = os.getcwd()[0:os.getcwd().rindex("stack-orchestrator")]
        print(f'Local stack dev_root_path (CERC_REPO_BASE_DIR) overridden to: {dev_root_path}')
    else:
        dev_root_path = os.path.expanduser(config("CERC_REPO_BASE_DIR", default="~/cerc"))

    build_root_path = os.path.join(dev_root_path, "build-trees")

    if verbose:
        print(f'Dev Root is: {dev_root_path}')

    if not os.path.isdir(dev_root_path):
        print('Dev root directory doesn\'t exist, creating')
        os.makedirs(dev_root_path)
    if not os.path.isdir(dev_root_path):
        print('Build root directory doesn\'t exist, creating')
        os.makedirs(build_root_path)

    # See: https://stackoverflow.com/a/20885799/1701505
    from . import data
    with importlib.resources.open_text(data, "npm-package-list.txt") as package_list_file:
        all_packages = package_list_file.read().splitlines()

    packages_in_scope = []
    if stack:
        stack_config = get_parsed_stack_config(stack)
        # TODO: syntax check the input here
        packages_in_scope = stack_config['npms']
    else:
        packages_in_scope = all_packages

    if verbose:
        print(f'Packages: {packages_in_scope}')

    def build_package(package):
        if not quiet:
            print(f"Building npm package: {package}")
        repo_dir = package
        repo_full_path = os.path.join(dev_root_path, repo_dir)
        # Copy the repo and build that to avoid propagating JS tooling file changes back into the cloned repo
        repo_copy_path = os.path.join(build_root_path, repo_dir)
        # First delete any old build tree
        if os.path.isdir(repo_copy_path):
            if verbose:
                print(f"Deleting old build tree: {repo_copy_path}")
            if not dry_run:
                rmtree(repo_copy_path)
        # Now copy the repo into the build tree location
        if verbose:
            print(f"Copying build tree from: {repo_full_path} to: {repo_copy_path}")
        if not dry_run:
            copytree(repo_full_path, repo_copy_path)
        build_command = ["sh", "-c", f"cd /workspace && build-npm-package-local-dependencies.sh {npm_registry_url}"]
        if not dry_run:
            if verbose:
                print(f"Executing: {build_command}")
            # Originally we used the PEP 584 merge operator:
            # envs = {"CERC_NPM_AUTH_TOKEN": npm_registry_url_token} | ({"CERC_SCRIPT_DEBUG": "true"} if debug else {})
            # but that isn't available in Python 3.8 (default in Ubuntu 20) so for now we use dict.update:
            envs = {"CERC_NPM_AUTH_TOKEN": npm_registry_url_token,
                    "LACONIC_HOSTED_CONFIG_FILE": "config-hosted.yml" # Convention used by our web app packages
                    }
            envs.update({"CERC_SCRIPT_DEBUG": "true"} if debug else {})
            try:
                docker.run(builder_js_image_name,
                           remove=True,
                           interactive=True,
                           tty=True,
                           user=f"{os.getuid()}:{os.getgid()}",
                           envs=envs,
                           # TODO: detect this host name in npm_registry_url rather than hard-wiring it
                           add_hosts=[("gitea.local", "host-gateway")],
                           volumes=[(repo_copy_path, "/workspace")],
                           command=build_command
                           )
                # Note that although the docs say that build_result should contain
                # the command output as a string, in reality it is always the empty string.
                # Since we detect errors via catching exceptions below, we can safely ignore it here.
            except DockerException as e:
                print(f"Error executing build for {package} in container:\n {e}")
                if not continue_on_error:
                    print("FATAL Error: build failed and --continue-on-error not set, exiting")
                    sys.exit(1)
                else:
                    print("****** Build Error, continuing because --continue-on-error is set")

        else:
            print("Skipped")

    for package in packages_in_scope:
        if include_exclude_check(package, include, exclude):
            build_package(package)
        else:
            if verbose:
                print(f"Excluding: {package}")


def _ensure_prerequisites():
    # Check that the builder-js container is available and
    # Tell the user how to build it if not
    images = docker.image.list(builder_js_image_name)
    if len(images) == 0:
        print(f"FATAL: builder image: {builder_js_image_name} is required but was not found")
        print("Please run this command to create it: laconic-so --stack build-support build-containers")
        sys.exit(1)
