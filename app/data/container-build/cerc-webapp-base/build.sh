#!/usr/bin/env bash
# Build cerc/laconic-registry-cli

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/webapp-base:local ${build_command_args} -f ${SCRIPT_DIR}/Dockerfile ${SCRIPT_DIR}
