#!/usr/bin/env bash
# Build cerc/cerc-plugeth-with-plugins
set -x

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/plugeth-with-plugins:local -f ${SCRIPT_DIR}/Dockerfile ${build_command_args} $SCRIPT_DIR
