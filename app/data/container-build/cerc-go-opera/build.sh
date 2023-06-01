#!/usr/bin/env bash
# Build cerc/go-opera
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
#cp ${CERC_REPO_BASE_DIR}/go-opera/docker/Dockerfile.opera ${CERC_REPO_BASE_DIR}/go-opera/Dockerfile
docker build -f ${CERC_REPO_BASE_DIR}/go-opera/docker/Dockerfile.opera -t cerc/go-opera:local ${build_command_args} ${CERC_REPO_BASE_DIR}/go-opera
