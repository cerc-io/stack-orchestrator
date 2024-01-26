#!/usr/bin/env bash
# Build the birbit image
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/birbit:local -f ${CERC_REPO_BASE_DIR}/birbit/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/birbit
