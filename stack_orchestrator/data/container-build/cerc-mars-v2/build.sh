#!/usr/bin/env bash
# Build the mars-v2 image
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/mars-v2:local -f ${CERC_REPO_BASE_DIR}/mars-v2-frontend/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/mars-v2-frontend
