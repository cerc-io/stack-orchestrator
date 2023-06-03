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
import sys


@click.group()
@click.option("--dir", required=True, help="path to deployment directory")
@click.pass_context
def command(ctx):
    print(f"Context: {ctx.parent.obj}")
    # Check that --stack wasn't supplied
    if ctx.parent.obj.stack:
        print("Error: --stack can't be supplied with the deployment command")
        sys.exit(1)


@command.command()
@click.pass_context
def up(ctx):
    print(f"Context: {ctx.parent.obj}")


@command.command()
@click.pass_context
def down(ctx):
    print(f"Context: {ctx.parent.obj}")


@command.command()
@click.pass_context
def ps(ctx):
    print(f"Context: {ctx.parent.obj}")


@command.command()
@click.pass_context
def logs(ctx):
    print(f"Context: {ctx.parent.obj}")


@command.command()
@click.pass_context
def task(ctx):
    print(f"Context: {ctx.parent.obj}")


@command.command()
@click.pass_context
def status(ctx):
    print(f"Context: {ctx.parent.obj}")
