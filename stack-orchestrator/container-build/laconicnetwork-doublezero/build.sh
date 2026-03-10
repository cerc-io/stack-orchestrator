#!/usr/bin/env bash

# Build laconicnetwork/doublezero
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

docker build -t laconicnetwork/doublezero:local \
  ${build_command_args} \
  -f ${CERC_CONTAINER_BASE_DIR}/laconicnetwork-doublezero/Dockerfile \
  ${CERC_CONTAINER_BASE_DIR}/laconicnetwork-doublezero
