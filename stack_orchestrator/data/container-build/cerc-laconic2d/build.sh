#!/usr/bin/env bash
# Build cerc/laconicd
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/laconic2d:local ${build_command_args} ${CERC_REPO_BASE_DIR}/laconic2d
