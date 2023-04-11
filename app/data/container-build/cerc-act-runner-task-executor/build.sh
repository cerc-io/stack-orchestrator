#!/usr/bin/env bash
# Build a local version of the task executor for act-runner
docker build -t cerc/act-runner-task-executor:local -f ${CERC_REPO_BASE_DIR}/hosting/gitea/Dockerfile.task-executor ${CERC_REPO_BASE_DIR}/hosting
