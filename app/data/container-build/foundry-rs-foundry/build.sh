#!/usr/bin/env bash
# Build foundry-rs/foundry
# HACK below : TARGETARCH needs to be derived from the host environment
docker build -t foundry-rs/foundry:local --build-arg TARGETARCH=arm64 ${CERC_REPO_BASE_DIR}/foundry
