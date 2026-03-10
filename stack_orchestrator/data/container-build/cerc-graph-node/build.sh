#!/usr/bin/env bash
# Build a local version of the graphprotocol/graph-node image (among reasons: the upstream image is not built for arm)
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/graph-node:local -f ${CERC_REPO_BASE_DIR}/graph-node/docker/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/graph-node
