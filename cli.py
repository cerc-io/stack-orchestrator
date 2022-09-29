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

import click

from app import setup_repositories
from app import build_containers
from app import deploy_system

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

class Options(object):
    def __init__(self, quiet, verbose, dry_run, local_stack):
        self.quiet = quiet
        self.verbose = verbose
        self.dry_run = dry_run
        self.local_stack = local_stack

@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--quiet', is_flag=True, default=False)
@click.option('--verbose', is_flag=True, default=False)
@click.option('--dry-run', is_flag=True, default=False)
@click.option('--local_stack', is_flag=True, default=False)

# See: https://click.palletsprojects.com/en/8.1.x/complex/#building-a-git-clone
@click.pass_context
def cli(ctx, quiet, verbose, dry_run, local_stack):
    """Laconic Stack Orchestrator"""
    ctx.obj = Options(quiet, verbose, dry_run, local_stack)

cli.add_command(setup_repositories.command,"setup-repositories")
cli.add_command(build_containers.command,"build-containers")
cli.add_command(deploy_system.command,"deploy-system")
