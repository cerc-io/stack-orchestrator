#!/usr/bin/env bash
# Build cerc/ipld-eth-beacon-indexer
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/ipld-eth-beacon-indexer:local ${build_command_args} ${CERC_REPO_BASE_DIR}/ipld-eth-beacon-indexer
