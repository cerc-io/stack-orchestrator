#!/usr/bin/env bash
# Build cerc/pocket
docker build -t cerc/pocket:local ${CERC_REPO_BASE_DIR}/pocket-core
