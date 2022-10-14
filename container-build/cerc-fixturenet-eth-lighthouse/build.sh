#!/usr/bin/env bash
# Build cerc/fixturenet-eth-lighthouse

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/fixturenet-eth-lighthouse:local -f ${SCRIPT_DIR}/Dockerfile $SCRIPT_DIR
