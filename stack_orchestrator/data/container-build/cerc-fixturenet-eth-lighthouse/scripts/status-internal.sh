#!/usr/bin/env bash
# Wrapper to facilitate using status.sh inside the container
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi
export LIGHTHOUSE_BASE_URL="http://fixturenet-eth-lighthouse-1:8001"
export GETH_BASE_URL="http://fixturenet-eth-geth-1:8545"
# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
$SCRIPT_DIR/status.sh
