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

# env vars:
# CERC_REPO_BASE_DIR defaults to ~/cerc

import os
import sys
from decouple import config
import git
from tqdm import tqdm
import click
import importlib.resources
from pathlib import Path
import yaml
from .util import include_exclude_check


class GitProgress(git.RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = tqdm(unit='B', ascii=True, unit_scale=True)

    def update(self, op_code, cur_count, max_count=None, message=''):
        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.refresh()


def is_git_repo(path):
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.exc.InvalidGitRepositoryError:
        return False

# TODO: find a place for this in the context of click
# parser = argparse.ArgumentParser(
#    epilog="Config provided either in .env or settings.ini or env vars: CERC_REPO_BASE_DIR (defaults to ~/cerc)"
#   )


@click.command()
@click.option("--include", help="only clone these repositories")
@click.option("--exclude", help="don\'t clone these repositories")
@click.option('--git-ssh', is_flag=True, default=False)
@click.option('--check-only', is_flag=True, default=False)
@click.option('--pull', is_flag=True, default=False)
@click.option('--branches-file', help="checkout branches specified in this file")
@click.pass_context
def command(ctx, include, exclude, git_ssh, check_only, pull, branches_file):
    '''git clone the set of repositories required to build the complete system from source'''

    quiet = ctx.obj.quiet
    verbose = ctx.obj.verbose
    dry_run = ctx.obj.dry_run
    stack = ctx.obj.stack

    branches = []

    # TODO: branches file needs to be re-worked in the context of stacks
    if branches_file:
        if verbose:
            print(f"loading branches from: {branches_file}")
        with open(branches_file) as branches_file_open:
            branches = branches_file_open.read().splitlines()
        if verbose:
            print(f"Branches are: {branches}")

    local_stack = ctx.obj.local_stack

    if local_stack:
        dev_root_path = os.getcwd()[0:os.getcwd().rindex("stack-orchestrator")]
        print(f"Local stack dev_root_path (CERC_REPO_BASE_DIR) overridden to: {dev_root_path}")
    else:
        dev_root_path = os.path.expanduser(config("CERC_REPO_BASE_DIR", default="~/cerc"))

    if not quiet:
        print(f"Dev Root is: {dev_root_path}")

    if not os.path.isdir(dev_root_path):
        if not quiet:
            print('Dev root directory doesn\'t exist, creating')
        os.makedirs(dev_root_path)

    # See: https://stackoverflow.com/a/20885799/1701505
    from . import data
    with importlib.resources.open_text(data, "repository-list.txt") as repository_list_file:
        all_repos = repository_list_file.read().splitlines()

    repos_in_scope = []
    if stack:
        # In order to be compatible with Python 3.8 we need to use this hack to get the path:
        # See: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure
        stack_file_path = Path(__file__).absolute().parent.joinpath("data", "stacks", stack, "stack.yml")
        with stack_file_path:
            stack_config = yaml.safe_load(open(stack_file_path, "r"))
            # TODO: syntax check the input here
            repos_in_scope = stack_config['repos']
    else:
        repos_in_scope = all_repos

    if verbose:
        print(f"Repos: {repos_in_scope}")
        if stack:
            print(f"Stack: {stack}")

    repos = []
    for repo in repos_in_scope:
        if include_exclude_check(repo, include, exclude):
            repos.append(repo)
        else:
            if verbose:
                print(f"Excluding: {repo}")

    def host_and_path_for_repo(fully_qualified_repo):
        repo_split = fully_qualified_repo.split("/")
        # Legacy unqualified repo means github
        if len(repo_split) == 2:
            return "github.com", "/".join(repo_split)
        else:
            if len(repo_split) == 3:
                # First part is the host
                return repo_split[0], "/".join(repo_split[1:])

    def process_repo(fully_qualified_repo):
        repo_host, repo_path = host_and_path_for_repo(fully_qualified_repo)
        git_ssh_prefix = f"git@{repo_host}:"
        git_http_prefix = f"https://{repo_host}/"
        full_github_repo_path = f"{git_ssh_prefix if git_ssh else git_http_prefix}{repo_path}"
        repoName = repo_path.split("/")[-1]
        full_filesystem_repo_path = os.path.join(dev_root_path, repoName)
        is_present = os.path.isdir(full_filesystem_repo_path)
        if not quiet:
            present_text = f"already exists active branch: {git.Repo(full_filesystem_repo_path).active_branch}" if is_present \
                else 'Needs to be fetched'
            print(f"Checking: {full_filesystem_repo_path}: {present_text}")
        # Quick check that it's actually a repo
        if is_present:
            if not is_git_repo(full_filesystem_repo_path):
                print(f"Error: {full_filesystem_repo_path} does not contain a valid git repository")
                sys.exit(1)
            else:
                if pull:
                    if verbose:
                        print(f"Running git pull for {full_filesystem_repo_path}")
                    if not check_only:
                        git_repo = git.Repo(full_filesystem_repo_path)
                        origin = git_repo.remotes.origin
                        origin.pull(progress=None if quiet else GitProgress())
                    else:
                        print("(git pull skipped)")
        if not is_present:
            # Clone
            if verbose:
                print(f'Running git clone for {full_github_repo_path} into {full_filesystem_repo_path}')
            if not dry_run:
                git.Repo.clone_from(full_github_repo_path,
                                    full_filesystem_repo_path,
                                    progress=None if quiet else GitProgress())
            else:
                print("(git clone skipped)")
        # Checkout the requested branch, if one was specified
        if branches:
            # Find the current repo in the branches list
            for repo_branch in branches:
                repo_branch_tuple = repo_branch.split(" ")
                if repo_branch_tuple[0] == repo:
                    # checkout specified branch
                    branch_to_checkout = repo_branch_tuple[1]
                    if verbose:
                        print(f"checking out branch {branch_to_checkout} in repo {repo}")
                        git_repo = git.Repo(full_filesystem_repo_path)
                        git_repo.git.checkout(branch_to_checkout)

    for repo in repos:
        try:
            process_repo(repo)
        except git.exc.GitCommandError as error:
            print(f"\n******* git command returned error exit status:\n{error}")
            sys.exit(1)
