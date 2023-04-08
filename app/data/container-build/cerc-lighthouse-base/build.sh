#!/usr/bin/env bash
# Build a local version of the sigp/lighthouse image
docker build -t cerc/lighthouse-base:local -f ${CERC_REPO_BASE_DIR}/lighthouse/Dockerfile ${CERC_REPO_BASE_DIR}/lighthouse
