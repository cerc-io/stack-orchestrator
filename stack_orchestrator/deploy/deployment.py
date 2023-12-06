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

import click
from pathlib import Path
import sys
from stack_orchestrator import constants
from stack_orchestrator.deploy.images import push_images_operation
from stack_orchestrator.deploy.deploy import up_operation, down_operation, ps_operation, port_operation
from stack_orchestrator.deploy.deploy import exec_operation, logs_operation, create_deploy_context
from stack_orchestrator.deploy.deploy_types import DeployCommandContext
from stack_orchestrator.deploy.deployment_context import DeploymentContext


@click.group()
@click.option("--dir", required=True, help="path to deployment directory")
@click.pass_context
def command(ctx, dir):
    '''manage a deployment'''

    # Check that --stack wasn't supplied
    if ctx.parent.obj.stack:
        print("Error: --stack can't be supplied with the deployment command")
        sys.exit(1)
    # Check dir is valid
    dir_path = Path(dir)
    if not dir_path.exists():
        print(f"Error: deployment directory {dir} does not exist")
        sys.exit(1)
    if not dir_path.is_dir():
        print(f"Error: supplied deployment directory path {dir} exists but is a file not a directory")
        sys.exit(1)
    # Store the deployment context for subcommands
    deployment_context = DeploymentContext()
    deployment_context.init(dir_path)
    ctx.obj = deployment_context


def make_deploy_context(ctx) -> DeployCommandContext:
    context: DeploymentContext = ctx.obj
    stack_file_path = context.get_stack_file()
    env_file = context.get_env_file()
    cluster_name = context.get_cluster_id()
    if constants.deploy_to_key in context.spec.obj:
        deployment_type = context.spec.obj[constants.deploy_to_key]
    else:
        deployment_type = constants.compose_deploy_type
    return create_deploy_context(ctx.parent.parent.obj, context, stack_file_path, None, None, cluster_name, env_file,
                                 deployment_type)


@command.command()
@click.option("--stay-attached/--detatch-terminal", default=False, help="detatch or not to see container stdout")
@click.argument('extra_args', nargs=-1)  # help: command: up <service1> <service2>
@click.pass_context
def up(ctx, stay_attached, extra_args):
    ctx.obj = make_deploy_context(ctx)
    services_list = list(extra_args) or None
    up_operation(ctx, services_list, stay_attached)


# start is the preferred alias for up
@command.command()
@click.option("--stay-attached/--detatch-terminal", default=False, help="detatch or not to see container stdout")
@click.argument('extra_args', nargs=-1)  # help: command: up <service1> <service2>
@click.pass_context
def start(ctx, stay_attached, extra_args):
    ctx.obj = make_deploy_context(ctx)
    services_list = list(extra_args) or None
    up_operation(ctx, services_list, stay_attached)


@command.command()
@click.option("--delete-volumes/--preserve-volumes", default=False, help="delete data volumes")
@click.argument('extra_args', nargs=-1)  # help: command: down <service1> <service2>
@click.pass_context
def down(ctx, delete_volumes, extra_args):
    # Get the stack config file name
    # TODO: add cluster name and env file here
    ctx.obj = make_deploy_context(ctx)
    down_operation(ctx, delete_volumes, extra_args)


# stop is the preferred alias for down
@command.command()
@click.option("--delete-volumes/--preserve-volumes", default=False, help="delete data volumes")
@click.argument('extra_args', nargs=-1)  # help: command: down <service1> <service2>
@click.pass_context
def stop(ctx, delete_volumes, extra_args):
    # TODO: add cluster name and env file here
    ctx.obj = make_deploy_context(ctx)
    down_operation(ctx, delete_volumes, extra_args)


@command.command()
@click.pass_context
def ps(ctx):
    ctx.obj = make_deploy_context(ctx)
    ps_operation(ctx)


@command.command()
@click.pass_context
def push_images(ctx):
    deploy_command_context: DeployCommandContext = make_deploy_context(ctx)
    deployment_context: DeploymentContext = ctx.obj
    push_images_operation(deploy_command_context, deployment_context)


@command.command()
@click.argument('extra_args', nargs=-1)  # help: command: port <service1> <service2>
@click.pass_context
def port(ctx, extra_args):
    port_operation(ctx, extra_args)


@command.command()
@click.argument('extra_args', nargs=-1)  # help: command: exec <service> <command>
@click.pass_context
def exec(ctx, extra_args):
    ctx.obj = make_deploy_context(ctx)
    exec_operation(ctx, extra_args)


@command.command()
@click.option("--tail", "-n", default=None, help="number of lines to display")
@click.option("--follow", "-f", is_flag=True, default=False, help="follow log output")
@click.argument('extra_args', nargs=-1)  # help: command: logs <service1> <service2>
@click.pass_context
def logs(ctx, tail, follow, extra_args):
    ctx.obj = make_deploy_context(ctx)
    logs_operation(ctx, tail, follow, extra_args)


@command.command()
@click.pass_context
def status(ctx):
    print(f"Context: {ctx.parent.obj}")
