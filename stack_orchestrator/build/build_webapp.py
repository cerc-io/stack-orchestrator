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

import os
from decouple import config
import click
from pathlib import Path
from stack_orchestrator.build import build_containers


@click.command()
@click.option('--base-container', default="cerc/nextjs-base")
@click.option('--source-repo', help="directory containing the webapp to build", required=True)
@click.option("--force-rebuild", is_flag=True, default=False, help="Override dependency checking -- always rebuild")
@click.option("--extra-build-args", help="Supply extra arguments to build")
@click.pass_context
def command(ctx, base_container, source_repo, force_rebuild, extra_build_args):
    '''build the specified webapp container'''

    quiet = ctx.obj.quiet
    verbose = ctx.obj.verbose
    dry_run = ctx.obj.dry_run
    debug = ctx.obj.debug
    local_stack = ctx.obj.local_stack
    stack = ctx.obj.stack
    continue_on_error = ctx.obj.continue_on_error

    # See: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure
    container_build_dir = Path(__file__).absolute().parent.parent.joinpath("data", "container-build")

    if local_stack:
        dev_root_path = os.getcwd()[0:os.getcwd().rindex("stack-orchestrator")]
        print(f'Local stack dev_root_path (CERC_REPO_BASE_DIR) overridden to: {dev_root_path}')
    else:
        dev_root_path = os.path.expanduser(config("CERC_REPO_BASE_DIR", default="~/cerc"))

    if not quiet:
        print(f'Dev Root is: {dev_root_path}')

    # First build the base container.
    container_build_env = build_containers.make_container_build_env(dev_root_path, container_build_dir, debug,
                                                                    force_rebuild, extra_build_args)

    build_containers.process_container(base_container, container_build_dir, container_build_env, dev_root_path, quiet,
                                       verbose, dry_run, continue_on_error)


    # Now build the target webapp.  We use the same build script, but with a different Dockerfile and work dir.
    container_build_env["CERC_WEBAPP_BUILD_RUNNING"] = "true"
    container_build_env["CERC_CONTAINER_BUILD_WORK_DIR"] = os.path.abspath(source_repo)
    container_build_env["CERC_CONTAINER_BUILD_DOCKERFILE"] = os.path.join(container_build_dir,
                                                                    base_container.replace("/", "-"),
                                                                    "Dockerfile.webapp")
    webapp_name = os.path.abspath(source_repo).split(os.path.sep)[-1]
    container_build_env["CERC_CONTAINER_BUILD_TAG"] = f"cerc/{webapp_name}:local"

    build_containers.process_container(base_container, container_build_dir, container_build_env, dev_root_path, quiet,
                                       verbose, dry_run, continue_on_error)
