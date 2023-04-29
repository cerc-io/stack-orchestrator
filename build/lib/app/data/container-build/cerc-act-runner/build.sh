#!/usr/bin/env bash
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
# Build a local version of the act-runner image
# TODO: enhance the default build code path to cope with this container (repo has an _ which needs to be converted to - in the image tag)
docker build -t cerc/act-runner:local -f ${CERC_REPO_BASE_DIR}/act_runner/Dockerfile ${build_command_args} ${CERC_REPO_BASE_DIR}/act_runner
