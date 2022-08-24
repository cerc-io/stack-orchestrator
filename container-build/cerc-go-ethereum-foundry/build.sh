#!/usr/bin/env bash
# Build cerc/go-ethereum-foundry

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/go-ethereum-foundry:local --build-arg GENESIS_FILE_PATH=genesis-automine.json ${SCRIPT_DIR}
