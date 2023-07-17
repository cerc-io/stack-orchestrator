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

import click
from dataclasses import dataclass
from pathlib import Path
import sys
from .deploy import up_operation, down_operation, ps_operation, port_operation, exec_operation, logs_operation, create_deploy_context
from .util import global_options


@dataclass
class DeploymentContext:
    dir: Path


@click.group()
@click.option("--dir", required=True, help="path to deployment directory")
@click.pass_context
def command(ctx, dir):
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
    ctx.obj = DeploymentContext(dir_path)


def make_deploy_context(ctx):
    # Get the stack config file name
    stack_file_path = ctx.obj.dir.joinpath("stack.yml")
    # TODO: add cluster name and env file here
    return create_deploy_context(ctx.parent.parent.obj, stack_file_path, None, None, None, None)


@command.command()
@click.argument('extra_args', nargs=-1)  # help: command: up <service1> <service2>
@click.pass_context
def up(ctx, extra_args):
    ctx.obj = make_deploy_context(ctx)
    services_list = list(extra_args) or None
    up_operation(ctx, services_list)


# start is the preferred alias for up
@command.command()
@click.argument('extra_args', nargs=-1)  # help: command: up <service1> <service2>
@click.pass_context
def start(ctx, extra_args):
    ctx.obj = make_deploy_context(ctx)
    services_list = list(extra_args) or None
    up_operation(ctx, services_list)


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
@click.argument('extra_args', nargs=-1)  # help: command: down <service1> <service2>
@click.pass_context
def stop(ctx, extra_args):
    # TODO: add cluster name and env file here
    ctx.obj = make_deploy_context(ctx)
    down_operation(ctx, extra_args, None)


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
@click.argument('extra_args', nargs=-1)  # help: command: logs <service1> <service2>
@click.pass_context
def logs(ctx, extra_args):
    ctx.obj = make_deploy_context(ctx)
    logs_operation(ctx, extra_args)


@command.command()
@click.pass_context
def status(ctx):
    print(f"Context: {ctx.parent.obj}")



#from importlib import resources, util
# TODO: figure out how to do this dynamically
#stack = "mainnet-laconic"
#module_name = "commands"
#spec = util.spec_from_file_location(module_name, "./app/data/stacks/" + stack + "/deploy/commands.py")
#imported_stack = util.module_from_spec(spec)
#spec.loader.exec_module(imported_stack)
#command.add_command(imported_stack.init)
#command.add_command(imported_stack.create)
