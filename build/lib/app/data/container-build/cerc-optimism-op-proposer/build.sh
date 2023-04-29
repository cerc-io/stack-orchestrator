#!/usr/bin/env bash

# Build cerc/optimism-op-proposer

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
docker build -t cerc/optimism-op-proposer:local -f ${SCRIPT_DIR}/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/optimism
