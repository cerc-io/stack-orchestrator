#!/usr/bin/env bash
# Build the ping pub image
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Two-stage build is to allow us to pick up both the upstream repo's files, and local files here for config
docker build -t cerc/ping-pub-base:local ${build_command_args} -f $SCRIPT_DIR/Dockerfile.base $CERC_REPO_BASE_DIR/cosmos-explorer
if [[ $? -ne 0 ]]; then
    echo "FATAL: Base container build failed, exiting"
    exit 1
fi
docker build -t cerc/ping-pub:local ${build_command_args} -f $SCRIPT_DIR/Dockerfile $SCRIPT_DIR
