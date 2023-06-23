#!/usr/bin/env bash
# Build a local version of the foundry-rs/foundry image
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/lasso:local -f ${CERC_REPO_BASE_DIR}/lasso/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/lasso
