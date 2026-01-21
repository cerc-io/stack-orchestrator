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

from stack_orchestrator.deploy.k8s.helpers import get_kind_cluster


@click.group()
@click.pass_context
def command(ctx):
    '''k8s cluster management commands'''
    pass


@command.group()
@click.pass_context
def list(ctx):
    '''list k8s resources'''
    pass


@list.command()
@click.pass_context
def cluster(ctx):
    '''Show the existing kind cluster'''
    existing_cluster = get_kind_cluster()
    if existing_cluster:
        print(existing_cluster)
    else:
        print("No cluster found")
