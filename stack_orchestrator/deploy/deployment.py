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
from stack_orchestrator.deploy.deploy import up_operation, down_operation, ps_operation, port_operation
from stack_orchestrator.deploy.deploy import exec_operation, logs_operation, create_deploy_context
from stack_orchestrator.deploy.stack import Stack
from stack_orchestrator.deploy.spec import Spec


class DeploymentContext:
    dir: Path
    spec: Spec
    stack: Stack

    def get_stack_file(self):
        return self.dir.joinpath("stack.yml")

    def get_spec_file(self):
        return self.dir.joinpath("spec.yml")

    def get_env_file(self):
        return self.dir.joinpath("config.env")

    # TODO: implement me
    def get_cluster_name(self):
        return None

    def init(self, dir):
        self.dir = dir
        self.stack = Stack()
        self.stack.init_from_file(self.get_stack_file())
        self.spec = Spec()
        self.spec.init_from_file(self.get_spec_file())


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


def make_deploy_context(ctx):
    context: DeploymentContext = ctx.obj
    stack_file_path = context.get_stack_file()
    env_file = context.get_env_file()
    cluster_name = context.get_cluster_name()
    return create_deploy_context(ctx.parent.parent.obj, stack_file_path, None, None, cluster_name, env_file,
                                 context.spec.obj["deploy-to"])


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
