#!/usr/bin/env bash
# Build the laconic.com image
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/laconic-dot-com:local -f ${CERC_REPO_BASE_DIR}/laconic.com/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/laconic.com
