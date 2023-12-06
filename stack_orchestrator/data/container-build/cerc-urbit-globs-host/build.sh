#!/usr/bin/env bash
# Build the urbit-globs-host image

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/urbit-globs-host:local -f ${SCRIPT_DIR}/Dockerfile ${build_command_args} ${SCRIPT_DIR}
