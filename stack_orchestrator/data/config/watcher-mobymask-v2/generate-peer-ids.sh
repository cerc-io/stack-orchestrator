#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

# Check for peer ids in ./peers folder, create if not present
if [ -f /peer-ids/relay-id.json ]; then
  echo "Using peer id for relay node from the mounted volume"
else
  echo "Creating a new peer id for relay node"
  yarn create-peer -f /peer-ids/relay-id.json
fi

if [ -f /peer-ids/peer-id.json ]; then
  echo "Using peer id for peer node from the mounted volume"
else
  echo "Creating a new peer id for peer node"
  yarn create-peer -f /peer-ids/peer-id.json
fi
