#!/usr/bin/env bash
# Build cerc/watcher-mobymask

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/watcher-mobymask:local -f ${SCRIPT_DIR}/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/watcher-ts

# TODO: add a mechanism to pass two repos into a container rather than the parent directory
