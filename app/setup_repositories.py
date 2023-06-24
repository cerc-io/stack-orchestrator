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


def branch_strip(s):
    return s.split('@')[0]


def host_and_path_for_repo(fully_qualified_repo):
    repo_branch_split = fully_qualified_repo.split("@")
    repo_branch = repo_branch_split[-1] if len(repo_branch_split) > 1 else None
    repo_host_split = repo_branch_split[0].split("/")
    # Legacy unqualified repo means github
    if len(repo_host_split) == 2:
        return "github.com", "/".join(repo_host_split), repo_branch
    else:
        if len(repo_host_split) == 3:
            # First part is the host
            return repo_host_split[0], "/".join(repo_host_split[1:]), repo_branch


# See: https://stackoverflow.com/questions/18659425/get-git-current-branch-tag-name
def _get_repo_current_branch_or_tag(full_filesystem_repo_path):
    current_repo_branch_or_tag = "***UNDETERMINED***"
    is_branch = False
    try:
        current_repo_branch_or_tag = git.Repo(full_filesystem_repo_path).active_branch.name
        is_branch = True
    except TypeError as error:
        # This means that the current ref is not a branch, so possibly a tag
        # Let's try to get the tag
        current_repo_branch_or_tag = git.Repo(full_filesystem_repo_path).git.describe("--tags", "--exact-match")
        # Note that git is assymetric -- the tag you told it to check out may not be the one
        # you get back here (if there are multiple tags associated with the same commit)
    return current_repo_branch_or_tag, is_branch


# TODO: fix the messy arg list here
def process_repo(verbose, quiet, dry_run, pull, check_only, git_ssh, dev_root_path, branches_array, fully_qualified_repo):
    if verbose:
        print(f"Processing repo: {fully_qualified_repo}")
    repo_host, repo_path, repo_branch = host_and_path_for_repo(fully_qualified_repo)
    git_ssh_prefix = f"git@{repo_host}:"
    git_http_prefix = f"https://{repo_host}/"
    full_github_repo_path = f"{git_ssh_prefix if git_ssh else git_http_prefix}{repo_path}"
    repoName = repo_path.split("/")[-1]
    full_filesystem_repo_path = os.path.join(dev_root_path, repoName)
    is_present = os.path.isdir(full_filesystem_repo_path)
    (current_repo_branch_or_tag, is_branch) = _get_repo_current_branch_or_tag(full_filesystem_repo_path) if is_present else (None, None)
    if not quiet:
        present_text = f"already exists active {'branch' if is_branch else 'tag'}: {current_repo_branch_or_tag}" if is_present \
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
                    if is_branch:
                        git_repo = git.Repo(full_filesystem_repo_path)
                        origin = git_repo.remotes.origin
                        origin.pull(progress=None if quiet else GitProgress())
                    else:
                        print(f"skipping pull because this repo checked out a tag")
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
    branch_to_checkout = None
    if branches_array:
        # Find the current repo in the branches list
        print("Checking")
        for repo_branch in branches_array:
            repo_branch_tuple = repo_branch.split(" ")
            if repo_branch_tuple[0] == branch_strip(fully_qualified_repo):
                # checkout specified branch
                branch_to_checkout = repo_branch_tuple[1]
    else:
        branch_to_checkout = repo_branch

    if branch_to_checkout:
        if current_repo_branch_or_tag is None or (current_repo_branch_or_tag and (current_repo_branch_or_tag != branch_to_checkout)):
            if not quiet:
                print(f"switching to branch {branch_to_checkout} in repo {repo_path}")
            git_repo = git.Repo(full_filesystem_repo_path)
            # git checkout works for both branches and tags
            git_repo.git.checkout(branch_to_checkout)
        else:
            if verbose:
                print(f"repo {repo_path} is already on branch/tag {branch_to_checkout}")


def parse_branches(branches_string):
    if branches_string:
        result_array = []
        branches_directives = branches_string.split(",")
        for branch_directive in branches_directives:
            split_directive = branch_directive.split("@")
            if len(split_directive) != 2:
                print(f"Error: branch specified is not valid: {branch_directive}")
                sys.exit(1)
            result_array.append(f"{split_directive[0]} {split_directive[1]}")
        return result_array
    else:
        return None


@click.command()
@click.option("--include", help="only clone these repositories")
@click.option("--exclude", help="don\'t clone these repositories")
@click.option('--git-ssh', is_flag=True, default=False)
@click.option('--check-only', is_flag=True, default=False)
@click.option('--pull', is_flag=True, default=False)
@click.option("--branches", help="override branches for repositories")
@click.option('--branches-file', help="checkout branches specified in this file")
@click.pass_context
def command(ctx, include, exclude, git_ssh, check_only, pull, branches, branches_file):
    '''git clone the set of repositories required to build the complete system from source'''

    quiet = ctx.obj.quiet
    verbose = ctx.obj.verbose
    dry_run = ctx.obj.dry_run
    stack = ctx.obj.stack

    branches_array = []

    # TODO: branches file needs to be re-worked in the context of stacks
    if branches_file:
        if branches:
            print("Error: can't specify both --branches and --branches-file")
            sys.exit(1)
        else:
            if verbose:
                print(f"loading branches from: {branches_file}")
            with open(branches_file) as branches_file_open:
                branches_array = branches_file_open.read().splitlines()

    print(f"branches: {branches}")
    if branches:
        if branches_file:
            print("Error: can't specify both --branches and --branches-file")
            sys.exit(1)
        else:
            branches_array = parse_branches(branches)

    if branches_array and verbose:
        print(f"Branches are: {branches_array}")

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
        if include_exclude_check(branch_strip(repo), include, exclude):
            repos.append(repo)
        else:
            if verbose:
                print(f"Excluding: {repo}")

    for repo in repos:
        try:
            process_repo(verbose, quiet, dry_run, pull, check_only, git_ssh, dev_root_path, branches_array, repo)
        except git.exc.GitCommandError as error:
            print(f"\n******* git command returned error exit status:\n{error}")
            sys.exit(1)
