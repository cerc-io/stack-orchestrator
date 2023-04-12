#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_RELAY_NODES="${CERC_RELAY_NODES:-${DEFAULT_CERC_RELAY_NODES}}"

# If not set (or []), check the mounted volume for relay peer id
if [ -z "$CERC_RELAY_NODES" ] || [ "$CERC_RELAY_NODES" = "[]" ]; then
  echo "CERC_RELAY_NODES not provided, taking from the mounted volume"
  CERC_RELAY_NODES="[\"/ip4/127.0.0.1/tcp/9090/ws/p2p/$(jq -r '.id' /peers/relay-id.json)\"]"
fi

echo "Using CERC_RELAY_NODES $CERC_RELAY_NODES"

# Set relay nodes in config from CERC_RELAY_NODES environment variable
jq --argjson relayNodes "$CERC_RELAY_NODES" \
  '.relayNodes = $relayNodes' \
  ./src/test-app-config.json > ./src/config.json

yarn build

serve -s build
