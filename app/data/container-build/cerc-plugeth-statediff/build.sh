#!/usr/bin/env bash
# Build cerc/plugeth-statediff
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/plugeth-statediff:local ${build_command_args} --build-arg GIT_VDBTO_TOKEN=${CERC_GO_AUTH_TOKEN} ${CERC_REPO_BASE_DIR}/plugeth-statediff
