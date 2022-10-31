#!/usr/bin/env bash
# Build cerc/test-container
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
docker build -t cerc/test-container:local -f ${SCRIPT_DIR}/Dockerfile $SCRIPT_DIR