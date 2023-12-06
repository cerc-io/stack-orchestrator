#!/usr/bin/env bash

# Build cerc/optimism-l2geth

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

docker build -t cerc/optimism-l2geth:local ${build_command_args} ${CERC_REPO_BASE_DIR}/op-geth
