#!/usr/bin/env bash
# Build the osmosis front end image
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/osmosis-front-end:local -f ${CERC_REPO_BASE_DIR}/osmosis-frontend/docker/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/osmosis-frontend
