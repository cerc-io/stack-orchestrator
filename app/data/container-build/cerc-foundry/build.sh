#!/usr/bin/env bash
# Build a local version of the foundry-rs/foundry image
docker build -t cerc/foundry:local -f ${CERC_REPO_BASE_DIR}/foundry/Dockerfile-debian ${CERC_REPO_BASE_DIR}/foundry
