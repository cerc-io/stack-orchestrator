#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_RELAY_NODES="${CERC_RELAY_NODES:-${DEFAULT_CERC_RELAY_NODES}}"
CERC_DENY_MULTIADDRS="${CERC_DENY_MULTIADDRS:-${DEFAULT_CERC_DENY_MULTIADDRS}}"

# If not set (or []), check the mounted volume for relay peer id
if [ -z "$CERC_RELAY_NODES" ] || [ "$CERC_RELAY_NODES" = "[]" ]; then
  echo "CERC_RELAY_NODES not provided, taking from the mounted volume"
  CERC_RELAY_NODES="[\"/ip4/127.0.0.1/tcp/9090/ws/p2p/$(jq -r '.id' /peers/relay-id.json)\"]"
fi

echo "Using CERC_RELAY_NODES $CERC_RELAY_NODES"

# Use yq to create config.yml with environment variables
yq -n ".relayNodes = strenv(CERC_RELAY_NODES)" > /config/config.yml
yq ".denyMultiaddrs = strenv(CERC_DENY_MULTIADDRS)" -i /config/config.yml

/scripts/start-serving-app.sh
