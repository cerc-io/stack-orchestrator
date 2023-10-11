#!/usr/bin/env bash
# Build cerc/plugeth
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
# Pass Go auth token if present
docker build -t cerc/plugeth:local ${build_command_args} --build-arg GIT_VDBTO_TOKEN=${CERC_GO_AUTH_TOKEN} ${CERC_REPO_BASE_DIR}/plugeth
