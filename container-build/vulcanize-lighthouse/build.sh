#!/usr/bin/env bash
# Build vulcanize/lighthouse

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build -t vulcanize/lighthouse:local ${SCRIPT_DIR}
