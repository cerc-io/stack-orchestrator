#!/usr/bin/env bash
# Build cerc/go-ethereum
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/go-ethereum:local ${build_command_args} ${CERC_REPO_BASE_DIR}/go-ethereum
