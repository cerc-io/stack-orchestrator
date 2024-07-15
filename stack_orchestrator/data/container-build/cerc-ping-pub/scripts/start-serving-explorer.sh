#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

${SCRIPT_DIR}/update-explorer-config.sh

echo "Starting serving explorer"
# Force cache re-build because vite is dumb and can't be restarted otherwise
yarn serve --host --force
