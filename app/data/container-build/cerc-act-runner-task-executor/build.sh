#!/usr/bin/env bash
# Build a local version of the task executor for act-runner
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/act-runner-task-executor:local -f ${CERC_REPO_BASE_DIR}/act_runner/Dockerfile.task-executor  ${build_command_args} ${CERC_REPO_BASE_DIR}/act_runner
