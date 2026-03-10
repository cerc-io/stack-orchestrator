#!/usr/bin/env bash
# Usage: tag_new_release.sh <major> <minor> <patch>
# Uses this script package to tag a new release:
# User must define: CERC_GH_RELEASE_SCRIPTS_DIR
# pointing to the location of that cloned repository
# e.g.
# cd ~/projects
# git clone https://github.com/cerc-io/github-release-api
# cd ./stack-orchestrator
# export CERC_GH_RELEASE_SCRIPTS_DIR=~/projects/github-release-api
# ./scripts/publish_shiv_package_github.sh
# TODO: check args and env vars
major=$1
minor=$2
patch=$3
export PATH=$CERC_GH_RELEASE_SCRIPTS_DIR:$PATH
git_tag_manager.sh -M ${major} -m ${minor} -p ${patch} -t "Release ${major}.${minor}.${patch}"
