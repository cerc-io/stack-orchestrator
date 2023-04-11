#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_RELAY_NODES="${CERC_RELAY_NODES:-${DEFAULT_CERC_RELAY_NODES}}"

# Set relay nodes in config from CERC_RELAY_NODES environment variable
jq --argjson relayNodes "$CERC_RELAY_NODES" \
  '.relayNodes = $relayNodes' \
  ./src/test-app-config.json > ./src/config.json

yarn build

serve -s build
