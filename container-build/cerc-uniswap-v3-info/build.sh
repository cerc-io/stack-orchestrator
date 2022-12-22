#!/usr/bin/env bash
# Build cerc/uniswap-v3-info

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/uniswap-v3-info:local -f ${SCRIPT_DIR}/Dockerfile ${CERC_REPO_BASE_DIR}/uniswap-v3-info
