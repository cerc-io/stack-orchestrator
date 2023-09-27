#!/usr/bin/env bash
# Build cerc/go-nitro

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

docker build -t cerc/go-nitro:local -f ${CERC_REPO_BASE_DIR}/go-nitro/docker/local/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/go-nitro
