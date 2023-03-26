#!/usr/bin/env bash
# Build cerc/optimism-op-batcher
# TODO: use upstream Dockerfile once its buildx-specific content has been removed
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
docker build -t cerc/optimism-op-batcher:local -f ${SCRIPT_DIR}/Dockerfile ${CERC_REPO_BASE_DIR}/optimism
