#!/usr/bin/env bash
# Build cerc/go-ethereum
docker build -t cerc/go-ethereum:local ${CERC_REPO_BASE_DIR}/go-ethereum
