#!/usr/bin/env bash

# Build cerc/optimism-op-node
# TODO: use upstream Dockerfile once its buildx-specific content has been removed

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
docker build -t cerc/optimism-op-node:local -f ${SCRIPT_DIR}/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/optimism
