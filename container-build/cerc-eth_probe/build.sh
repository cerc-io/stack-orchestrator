#!/usr/bin/env bash
# Build cerc/eth-probe
docker build -t cerc/eth-probe:local ${CERC_REPO_BASE_DIR}/eth_probe
