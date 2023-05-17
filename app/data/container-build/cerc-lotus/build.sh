#!/usr/bin/env bash
# Build cerc/lotus
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Per lotus docs, 'releases' branch always contains latest stable release
git -C ${CERC_REPO_BASE_DIR}/lotus checkout releases

# Replace repo's Dockerfile with modified one
cp ${SCRIPT_DIR}/Dockerfile ${CERC_REPO_BASE_DIR}/lotus/Dockerfile

docker build -t cerc/lotus:local ${build_command_args} ${CERC_REPO_BASE_DIR}/lotus
