# env vars:
# DEV_ROOT defaults to ~/vulcanize

import os
import argparse
from pydoc import ispackage
from decouple import config
import git

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

dev_root_path = config("DEV_ROOT", default="~/vulcanize")

if not args.quiet:
    print(f'Dev Root is: {dev_root_path}')

with open("repository-list.txt") as repositoryListFile:
    repos = repositoryListFile.read().splitlines()

if verbose:
    print (f'Repos: {repos}')

# Ok, now we can go ahead and look to see which if any of the repos are already cloned

def processRepo(repo):
    full_github_repo_path = f'git@github.com:{repo}'
    repoName = repo.split("/")[-1]
    fullFilesystemRepoPath = os.path.join(dev_root_path, repoName)
    isPresent = os.path.isdir(fullFilesystemRepoPath)
    print(f'Checking: {fullFilesystemRepoPath}, exists: {isPresent}')
    if not isPresent:
        # Clone
        if not quiet:
            print(f'Running git clone for {full_github_repo_path} into {fullFilesystemRepoPath}')
        if not args.check_only:
            git.Repo.clone_from(full_github_repo_path, fullFilesystemRepoPath)
        else:
            print("(git clone skipped)")


for repo in repos:
    processRepo(repo)
