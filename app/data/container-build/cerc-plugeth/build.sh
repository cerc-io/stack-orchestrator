#!/usr/bin/env bash
# Build cerc/plugeth
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
# Pass Go auth token if present
if [[ -n "${CERC_GO_AUTH_TOKEN}" ]]; then
    build_command_args="${build_command_args} --build-arg GIT_VDBTO_TOKEN=${CERC_GO_AUTH_TOKEN}"
fi
docker build -t cerc/plugeth:local ${build_command_args} ${CERC_REPO_BASE_DIR}/plugeth
