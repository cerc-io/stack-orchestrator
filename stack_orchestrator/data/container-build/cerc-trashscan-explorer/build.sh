#!/usr/bin/env bash
# Build the TrashScan Explorer image
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Two-stage build: base image from repo, final image with local scripts
docker build -t cerc/trashscan-explorer-base:local \
    ${build_command_args} \
    -f ${SCRIPT_DIR}/Dockerfile.base \
    ${CERC_REPO_BASE_DIR}/TrashScan-Explorer

if [[ $? -ne 0 ]]; then
    echo "FATAL: Base container build failed, exiting"
    exit 1
fi

docker build -t cerc/trashscan-explorer:local \
    ${build_command_args} \
    -f ${SCRIPT_DIR}/Dockerfile \
    ${SCRIPT_DIR}
