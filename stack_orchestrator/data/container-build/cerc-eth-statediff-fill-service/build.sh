#!/usr/bin/env bash
# Build cerc/eth-statediff-fill-service
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/eth-statediff-fill-service:local ${build_command_args} ${CERC_REPO_BASE_DIR}/eth-statediff-fill-service
