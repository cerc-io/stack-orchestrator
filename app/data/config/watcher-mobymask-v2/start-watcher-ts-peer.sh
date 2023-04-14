#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

# Check for peer ids in ./peers folder, create if not present
if [ -f ./relay-id.json ]; then
  echo "Using peer id for relay node from the mounted volume"
else
  echo "Creating a new peer id for relay node"
  yarn create-peer -f relay-id.json
fi

if [ -f ./peer-id.json ]; then
  echo "Using peer id for peer node from the mounted volume"
else
  echo "Creating a new peer id for peer node"
  yarn create-peer -f peer-id.json
fi

CERC_RELAY_MULTIADDR="/dns4/mobymask-watcher-server/tcp/9090/ws/p2p/$(jq -r '.id' ./relay-id.json)"

# Write the relay node's multiaddr to /app/packages/peer/.env for running tests
echo "RELAY=\"$CERC_RELAY_MULTIADDR\"" > ./.env
