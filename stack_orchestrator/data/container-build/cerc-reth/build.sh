#!/usr/bin/env bash
# Build cerc/go-opera
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

docker build -t cerc/reth:local ${build_command_args} ${CERC_REPO_BASE_DIR}/reth
