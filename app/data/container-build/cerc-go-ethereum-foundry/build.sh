#!/usr/bin/env bash
# Build cerc/go-ethereum-foundry

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/go-ethereum-foundry:local --build-arg GENESIS_FILE_PATH=genesis-automine.json ${build_command_args} ${SCRIPT_DIR}
