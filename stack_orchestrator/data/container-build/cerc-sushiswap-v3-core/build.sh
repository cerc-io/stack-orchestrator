#!/usr/bin/env bash

# Build cerc/sushiswap-v3-core
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/sushiswap-v3-core:local -f ${SCRIPT_DIR}/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/sushiswap-v3-core
