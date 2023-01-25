#!/usr/bin/env bash
# Usage: publish_shiv_package_github.sh <major> <minor> <patch>
# Uses this script package to publish a new release:
# https://github.com/cerc-io/github-release-api
# User must define: CERC_GH_RELEASE_SCRIPTS_DIR
# pointing to the location of that cloned repository
# e.g. 
# cd ~/projects
# git clone https://github.com/cerc-io/github-release-api
# cd ./stack-orchestrator
# export CERC_GH_RELEASE_SCRIPTS_DIR=~/projects/github-release-api
# ./scripts/publish_shiv_package_github.sh
# In addition, a valid GitHub token must be defined in
# CERC_PACKAGE_RELEASE_GITHUB_TOKEN
# TODO: check args and env vars
major=$1
minor=$2
patch=$3
export PATH=$CERC_GH_RELEASE_SCRIPTS_DIR:$PATH
git_tag_manager.sh -M ${major} -m ${minor} -p ${patch} -t "Release ${major}.${minor}.${patch}"
github_release_manager.sh \
        -l david@bozemanpass.com -t ${CERC_PACKAGE_RELEASE_GITHUB_TOKEN} \
        -o cerc-io -r stack-orchestrator \
        -d v${major}.${minor}.${patch} \
        -c create
github_release_manager.sh \
        -l david@bozemanpass.com -t ${CERC_PACKAGE_RELEASE_GITHUB_TOKEN} \
        -o cerc-io -r stack-orchestrator \
        -d v${major}.${minor}.${patch} \
        -c upload ./package/laconic-so
