#!/usr/bin/env bash
# Build cerc/nginx

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t cerc/nginx:local ${SCRIPT_DIR}
