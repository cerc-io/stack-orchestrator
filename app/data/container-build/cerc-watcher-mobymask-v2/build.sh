#!/usr/bin/env bash
# Build cerc/watcher-mobymask-v2

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/watcher-mobymask-v2:local -f ${SCRIPT_DIR}/Dockerfile ${CERC_REPO_BASE_DIR}/watcher-ts
