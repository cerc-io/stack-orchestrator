#!/usr/bin/env bash
# Build cerc/optimism-l2geth
docker build -t cerc/optimism-l2geth:local ${CERC_REPO_BASE_DIR}/op-geth
