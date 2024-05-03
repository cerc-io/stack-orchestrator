#!/usr/bin/env bash
# Build cerc/mainnet-lotus
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

git stash

# Use a release version tag to match the modified Dockerfile replaced in next step
git -C ${CERC_REPO_BASE_DIR}/lotus checkout v1.27.0-rc1-c

# Replace repo's Dockerfile with modified one
cp ${SCRIPT_DIR}/Dockerfile ${CERC_REPO_BASE_DIR}/lotus/Dockerfile

docker build -t cerc/lotus-mainnet:local ${build_command_args} ${CERC_REPO_BASE_DIR}/lotus