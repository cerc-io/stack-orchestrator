#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

RELAY_NODES="${RELAY_NODES:-${DEFAULT_RELAY_NODES}}"

# Set relay nodes in config from RELAY_NODES environment variable
jq --argjson relayNodes "$RELAY_NODES" \
  '.relayNodes = $relayNodes' \
  ./src/test-app-config.json > ./src/config.json

yarn build

serve -s build
