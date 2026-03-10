#!/usr/bin/env bash
# Build cerc/tx-spammer
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/tx-spammer:local ${build_command_args} ${CERC_REPO_BASE_DIR}/tx-spammer
