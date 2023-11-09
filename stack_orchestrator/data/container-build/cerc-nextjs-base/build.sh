#!/usr/bin/env bash
# Build cerc/laconic-registry-cli

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

CERC_CONTAINER_BUILD_WORK_DIR=${CERC_CONTAINER_BUILD_WORK_DIR:-$SCRIPT_DIR}
CERC_CONTAINER_BUILD_DOCKERFILE=${CERC_CONTAINER_BUILD_DOCKERFILE:-$SCRIPT_DIR/Dockerfile}
CERC_CONTAINER_BUILD_TAG=${CERC_CONTAINER_BUILD_TAG:-cerc/nextjs-base:local}

docker build -t $CERC_CONTAINER_BUILD_TAG ${build_command_args} -f $CERC_CONTAINER_BUILD_DOCKERFILE $CERC_CONTAINER_BUILD_WORK_DIR
