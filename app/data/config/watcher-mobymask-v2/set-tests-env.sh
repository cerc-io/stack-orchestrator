#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_RELAY_MULTIADDR="/dns4/mobymask-watcher-server/tcp/9090/ws/p2p/$(jq -r '.id' /peer-ids/relay-id.json)"

# Write the relay node's multiaddr to /app/packages/peer/.env for running tests
echo "RELAY=\"$CERC_RELAY_MULTIADDR\"" > ./.env
