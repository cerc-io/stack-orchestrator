#!/usr/bin/env bash
# Build a local version of the task executor for act-runner
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
docker build -t cerc/act-runner-task-executor:local -f ${CERC_REPO_BASE_DIR}/hosting/act-runner/Dockerfile.task-executor ${build_command_args} ${SCRIPT_DIR}
