#!/usr/bin/env bash
# Build a local version of the task executor for act_runner
docker build -t cerc/act_runner-task-executor:local -f ${CERC_REPO_BASE_DIR}/act_runner/Dockerfile.task-executor ${CERC_REPO_BASE_DIR}/act_runner
