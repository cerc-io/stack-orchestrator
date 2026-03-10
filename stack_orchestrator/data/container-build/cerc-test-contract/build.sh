#!/usr/bin/env bash
# Build cerc/test-contract
source ${CERC_CONTAINER_BASE_DIR}/build-base.sh
docker build -t cerc/test-contract:local --build-arg ETH_ADDR=http://go-ethereum:8545 ${build_command_args} ${CERC_REPO_BASE_DIR}/ipld-eth-db-validator/test/contract
