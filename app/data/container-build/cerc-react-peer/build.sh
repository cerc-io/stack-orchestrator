#!/usr/bin/env bash
# Build cerc/react-peer

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

CERC_NPM_REGISTRY_URL="https://git.vdb.to/api/packages/cerc-io/npm/"

docker build -t cerc/react-peer:local  ${build_command_args} -f ${SCRIPT_DIR}/Dockerfile \
  --build-arg CERC_NPM_REGISTRY_URL ${SCRIPT_DIR}
