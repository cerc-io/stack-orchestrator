#!/usr/bin/env bash
# Build cerc/keycloak-reg-ui

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/keycloak-reg-ui:local ${build_command_args} ${CERC_REPO_BASE_DIR}/keycloak-reg-ui
