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

# env vars:
# CERC_REPO_BASE_DIR defaults to ~/cerc


import click
import os

from decouple import config
from git import exc

from stack_orchestrator.opts import opts
from stack_orchestrator.repos.setup_repositories import process_repo
from stack_orchestrator.util import error_exit


@click.command()
@click.argument('stack-locator')
@click.option('--git-ssh', is_flag=True, default=False)
@click.option('--check-only', is_flag=True, default=False)
@click.option('--pull', is_flag=True, default=False)
@click.pass_context
def command(ctx, stack_locator, git_ssh, check_only, pull):
    '''optionally resolve then git clone a repository containing one or more stack definitions'''
    dev_root_path = os.path.expanduser(config("CERC_REPO_BASE_DIR", default="~/cerc"))
    if not opts.o.quiet:
        print(f"Dev Root is: {dev_root_path}")
    try:
        process_repo(pull, check_only, git_ssh, dev_root_path, None, stack_locator)
    except exc.GitCommandError as error:
        error_exit(f"\n******* git command returned error exit status:\n{error}")
