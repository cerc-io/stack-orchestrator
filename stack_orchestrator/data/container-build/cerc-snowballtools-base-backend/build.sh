#!/usr/bin/env bash
# Build cerc/webapp-deployer-backend

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/snowballtools-base-backend-base:local ${build_command_args} -f ${SCRIPT_DIR}/Dockerfile-base ${CERC_REPO_BASE_DIR}/snowballtools-base
docker build -t cerc/snowballtools-base-backend:local ${build_command_args} ${SCRIPT_DIR} 
