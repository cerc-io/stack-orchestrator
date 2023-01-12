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

import os
from decouple import config
import click
import importlib.resources
from python_on_whales import docker
from .util import include_exclude_check

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
    with importlib.resources.open_text(data, "npm-package-list.txt") as package_list_file:
        packages = package_list_file.read().splitlines()

    if verbose:
        print(f'Packages: {packages}')

    def build_package(package):
        if not quiet:
            print(f"Building npm package: {package}")
        repo_dir = package
        repo_full_path = os.path.join(dev_root_path, repo_dir)
        # TODO: make the npm registry url configurable.
        build_command = ["sh", "-c", "cd /workspace && build-npm-package-local-dependencies.sh http://gitea.local:3000/api/packages/cerc-io/npm/"]
        if not dry_run:
            if verbose:
                print(f"Executing: {build_command}")
            envs = {"CERC_NPM_AUTH_TOKEN": os.environ["CERC_NPM_AUTH_TOKEN"]} | ({"CERC_SCRIPT_DEBUG": "true"} if debug else {})
            build_result = docker.run("cerc/builder-js",
                                      remove=True,
                                      interactive=True,
                                      tty=True,
                                      user=f"{os.getuid()}:{os.getgid()}",
                                      envs=envs,
                                      add_hosts=[("gitea.local", "host-gateway")],
                                      volumes=[(repo_full_path, "/workspace")],
                                      command=build_command
                                      )
            # TODO: check result in build_result.returncode
            print(f"Result is: {build_result}")
        else:
            print("Skipped")

    for package in packages:
        if include_exclude_check(package, include, exclude):
            build_package(package)
        else:
            if verbose:
                print(f"Excluding: {package}")
