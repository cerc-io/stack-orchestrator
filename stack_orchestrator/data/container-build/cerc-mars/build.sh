#!/usr/bin/env bash
# Build the mars image
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/mars:local -f ${CERC_REPO_BASE_DIR}/mars-interface/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/mars-interface
