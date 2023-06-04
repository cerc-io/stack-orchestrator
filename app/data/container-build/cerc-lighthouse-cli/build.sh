#!/usr/bin/env bash
# Build cerc/lighthouse-cli

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

project_dir=${CERC_REPO_BASE_DIR}/lighthouse
docker build -t cerc/lighthouse-cli:local -f ${project_dir}/lcli/Dockerfile ${build_command_args} ${project_dir}
