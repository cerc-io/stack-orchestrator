#!/usr/bin/env bash
# Build cerc/plugeth
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
# This container build currently requires access to private dependencies in gitea
# so we check that the necessary access token has been supplied here, then pass it o the build
if [[ -z "${CERC_GO_AUTH_TOKEN}" ]]; then
    echo "ERROR: CERC_GO_AUTH_TOKEN is not set" >&2
    exit 1
fi
docker build -t cerc/plugeth:local ${build_command_args} --build-arg GIT_VDBTO_TOKEN=${CERC_GO_AUTH_TOKEN} ${CERC_REPO_BASE_DIR}/plugeth
