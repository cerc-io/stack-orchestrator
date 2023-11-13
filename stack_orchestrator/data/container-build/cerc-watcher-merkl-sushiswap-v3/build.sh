#!/usr/bin/env bash
# Build cerc/watcher-merkl-sushiswap-v3

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/my-new-stack:local -f ${CERC_REPO_BASE_DIR}/my-new-stack/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/my-new-stack

docker build -t cerc/watcher-merkl-sushiswap-v3:local -f ${SCRIPT_DIR}/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/merkl-sushiswap-v3-watcher-ts
