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
import sys

from decouple import config
import click
from pathlib import Path
from stack_orchestrator.build import build_containers
from stack_orchestrator.deploy.webapp.util import determine_base_container, TimedLogger
from stack_orchestrator.build.build_types import BuildContext


@click.command()
@click.option('--base-container')
@click.option('--source-repo', help="directory containing the webapp to build", required=True)
@click.option("--force-rebuild", is_flag=True, default=False, help="Override dependency checking -- always rebuild")
@click.option("--extra-build-args", help="Supply extra arguments to build")
@click.option("--tag", help="Container tag (default: cerc/<app_name>:local)")
@click.pass_context
def command(ctx, base_container, source_repo, force_rebuild, extra_build_args, tag):
    '''build the specified webapp container'''
    logger = TimedLogger()

    quiet = ctx.obj.quiet
    debug = ctx.obj.debug
    verbose = ctx.obj.verbose
    local_stack = ctx.obj.local_stack
    stack = ctx.obj.stack

    # See: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure
    container_build_dir = Path(__file__).absolute().parent.parent.joinpath("data", "container-build")

    if local_stack:
        dev_root_path = os.getcwd()[0:os.getcwd().rindex("stack-orchestrator")]
        logger.log(f'Local stack dev_root_path (CERC_REPO_BASE_DIR) overridden to: {dev_root_path}')
    else:
        dev_root_path = os.path.expanduser(config("CERC_REPO_BASE_DIR", default="~/cerc"))

    if verbose:
        logger.log(f'Dev Root is: {dev_root_path}')

    if not base_container:
        base_container = determine_base_container(source_repo)

    # First build the base container.
    container_build_env = build_containers.make_container_build_env(dev_root_path, container_build_dir, debug,
                                                                    force_rebuild, extra_build_args)

    if verbose:
        logger.log(f"Building base container: {base_container}")

    build_context_1 = BuildContext(
        stack,
        base_container,
        container_build_dir,
        container_build_env,
        dev_root_path,
    )
    ok = build_containers.process_container(build_context_1)
    if not ok:
        logger.log("ERROR: Build failed.")
        sys.exit(1)

    if verbose:
        logger.log(f"Base container {base_container} build finished.")

    # Now build the target webapp.  We use the same build script, but with a different Dockerfile and work dir.
    container_build_env["CERC_WEBAPP_BUILD_RUNNING"] = "true"
    container_build_env["CERC_CONTAINER_BUILD_WORK_DIR"] = os.path.abspath(source_repo)
    container_build_env["CERC_CONTAINER_BUILD_DOCKERFILE"] = os.path.join(container_build_dir,
                                                                          base_container.replace("/", "-"),
                                                                          "Dockerfile.webapp")
    if not tag:
        webapp_name = os.path.abspath(source_repo).split(os.path.sep)[-1]
        tag = f"cerc/{webapp_name}:local"

    container_build_env["CERC_CONTAINER_BUILD_TAG"] = tag

    if verbose:
        logger.log(f"Building app container: {tag}")

    build_context_2 = BuildContext(
        stack,
        base_container,
        container_build_dir,
        container_build_env,
        dev_root_path,
    )
    ok = build_containers.process_container(build_context_2)
    if not ok:
        logger.log("ERROR: Build failed.")
        sys.exit(1)

    if verbose:
        logger.log(f"App container {base_container} build finished.")
        logger.log("build-webapp complete", show_step_time=False, show_total_time=True)
