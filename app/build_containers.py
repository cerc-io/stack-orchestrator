# Copyright © 2022 Cerc

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

# TODO: display the available list of containers; allow re-build of either all or specific containers

import os
from decouple import config
import subprocess
import click
import importlib.resources
from pathlib import Path
from .util import include_exclude_check

# TODO: find a place for this
#    epilog="Config provided either in .env or settings.ini or env vars: CERC_REPO_BASE_DIR (defaults to ~/cerc)"


@click.command()
@click.option('--include', help="only build these containers")
@click.option('--exclude', help="don\'t build these containers")
@click.pass_context
def command(ctx, include, exclude):
    '''build the set of containers required for a complete stack'''

    quiet = ctx.obj.quiet
    verbose = ctx.obj.verbose
    dry_run = ctx.obj.dry_run
    local_stack = ctx.obj.local_stack

    # See: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure
    container_build_dir = Path(__file__).absolute().parent.joinpath("data", "container-build")

    if local_stack:
        dev_root_path = os.getcwd()[0:os.getcwd().rindex("stack-orchestrator")]
        print(f'Local stack dev_root_path (CERC_REPO_BASE_DIR) overridden to: {dev_root_path}')
    else:
        dev_root_path = os.path.expanduser(config("CERC_REPO_BASE_DIR", default="~/cerc"))

    if not quiet:
        print(f'Dev Root is: {dev_root_path}')

    if not os.path.isdir(dev_root_path):
        print('Dev root directory doesn\'t exist, creating')

    # See: https://stackoverflow.com/a/20885799/1701505
    from . import data
    with importlib.resources.open_text(data, "container-image-list.txt") as container_list_file:
        containers = container_list_file.read().splitlines()

    if verbose:
        print(f'Containers: {containers}')

    # TODO: make this configurable
    container_build_env = {
        "CERC_NPM_URL": "http://gitea.local:3000/api/packages/cerc-io/npm/",
        "CERC_NPM_AUTH_TOKEN": config("CERC_NPM_AUTH_TOKEN", default="<token-not-supplied>"),
        "CERC_REPO_BASE_DIR": dev_root_path
    }

    def process_container(container):
        if not quiet:
            print(f"Building: {container}")
        build_dir = os.path.join(container_build_dir, container.replace("/", "-"))
        build_script_filename = os.path.join(build_dir, "build.sh")
        if verbose:
            print(f"Build script filename: {build_script_filename}")
        if os.path.exists(build_script_filename):
            build_command = build_script_filename
        else:
            if verbose:
                print(f"No script file found: {build_script_filename}, using default build script")
            repo_dir = container.split('/')[1]
            # TODO: make this less of a hack -- should be specified in some metadata somewhere
            # Check if we have a repo for this container. If not, set the context dir to the container-build subdir
            repo_full_path = os.path.join(dev_root_path, repo_dir)
            repo_dir_or_build_dir = repo_dir if os.path.exists(repo_full_path) else build_dir
            build_command = os.path.join(container_build_dir, "default-build.sh") + f" {container} {repo_dir_or_build_dir}"
        if not dry_run:
            if verbose:
                print(f"Executing: {build_command}")
            build_result = subprocess.run(build_command, shell=True, env=container_build_env)
            # TODO: check result in build_result.returncode
            print(f"Result is: {build_result}")
        else:
            print("Skipped")

    for container in containers:
        if include_exclude_check(container, include, exclude):
            process_container(container)
        else:
            if verbose:
                print(f"Excluding: {container}")
