#!/usr/bin/env bash
# Build cerc/optimism-contracts

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/optimism-contracts:local -f ${SCRIPT_DIR}/Dockerfile \
  --add-host gitea.local:host-gateway \
  --build-arg CERC_NPM_AUTH_TOKEN --build-arg CERC_NPM_URL ${SCRIPT_DIR}
