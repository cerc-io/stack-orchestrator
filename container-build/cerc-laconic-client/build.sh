#!/usr/bin/env bash
# Build cerc/laconic-client
set -x
# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/laconic-client:local -f ${SCRIPT_DIR}/Dockerfile --build-arg NPM_AUTH_TOKEN=$(NPM_AUTH_TOKEN) ${CERC_REPO_BASE_DIR}/laconic-client
