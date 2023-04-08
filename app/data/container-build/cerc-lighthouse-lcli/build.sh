#!/usr/bin/env bash
# Build a local version of the sigp/lcli image
docker build -t cerc/lighthouse-lcli:local -f ${CERC_REPO_BASE_DIR}/lighthouse/lcli/Dockerfile ${CERC_REPO_BASE_DIR}/lighthouse
