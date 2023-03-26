#!/usr/bin/env bash
# Build a local version of the act-runner image
docker build -t cerc/act-runner:local -f ${CERC_REPO_BASE_DIR}/act_runner/Dockerfile ${CERC_REPO_BASE_DIR}/act_runner
