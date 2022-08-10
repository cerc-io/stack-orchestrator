# env vars:
# DEV_ROOT defaults to ~/vulcanize

import os
import sys
import argparse
from pydoc import ispackage
from decouple import config
import git
from tqdm import tqdm

class CloneProgress(git.RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = tqdm(unit = 'B', ascii = True, unit_scale = True)

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

parser = argparse.ArgumentParser(
    description="git clone the set of repositories required to build the complete system from source",
    epilog="Config provided either in .env or settings.ini or env vars: DEV_ROOT (defaults to ~/vulcanize)"
    )
parser.add_argument("--verbose", action="store_true", help="increase output verbosity")
parser.add_argument("--quiet", action="store_true", help="don\'t print informational output")
parser.add_argument("--check-only", action="store_true", help="looks at what\'s already there and checks if it looks good")
parser.add_argument("--dry-run", action="store_true", help="don\'t do anything, just print the commands that would be executed")

args = parser.parse_args()
print(args)

verbose = args.verbose
quiet = args.quiet

dev_root_path = os.path.expanduser(config("DEV_ROOT", default="~/vulcanize"))

if not args.quiet:
    print(f'Dev Root is: {dev_root_path}')

if not os.path.isdir(dev_root_path):
    if not quiet:
        print(f'Dev root directory doesn\'t exist, creating')
    os.makedirs(dev_root_path)

with open("repository-list.txt") as repositoryListFile:
    repos = repositoryListFile.read().splitlines()

if verbose:
    print (f'Repos: {repos}')

# Ok, now we can go ahead and look to see which if any of the repos are already cloned

def processRepo(repo):
    full_github_repo_path = f'git@github.com:{repo}'
    repoName = repo.split("/")[-1]
    full_filesystem_repo_path = os.path.join(dev_root_path, repoName)
    is_present = os.path.isdir(full_filesystem_repo_path)
    if not quiet:
        present_text = f'already exists active branch: {git.Repo(full_filesystem_repo_path).active_branch}' if is_present else 'Needs to be fetched'
        print(f'Checking: {full_filesystem_repo_path}: {present_text}')
    # Quick check that it's actually a repo
    if is_present:
        if not is_git_repo(full_filesystem_repo_path):
            print(f'Error: {full_filesystem_repo_path} does not contain a valid git repository')
            sys.exit(1) 
    if not is_present:
        # Clone
        if verbose:
            print(f'Running git clone for {full_github_repo_path} into {full_filesystem_repo_path}')
        if not args.check_only:
            git.Repo.clone_from(full_github_repo_path, full_filesystem_repo_path, 
            progress = None if quiet else CloneProgress())
        else:
            print("(git clone skipped)")


for repo in repos:
    processRepo(repo)
