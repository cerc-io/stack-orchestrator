#!/usr/bin/env bash
# Build the ping pub image
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

docker build -t cerc/ping-pub:local ${build_command_args} -f $CERC_REPO_BASE_DIR/explorer/Dockerfile $CERC_REPO_BASE_DIR/explorer
