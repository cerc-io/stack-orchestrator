#!/usr/bin/env bash
# Build cerc/plugeth
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/plugeth:local ${build_command_args} ${CERC_REPO_BASE_DIR}/plugeth
