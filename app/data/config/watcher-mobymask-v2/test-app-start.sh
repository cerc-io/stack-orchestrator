#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi


jq --argjson relayNodes "$RELAY_NODES" \
  '.relayNodes = $relayNodes' \
  ./src/test-app-config.json > ./src/config.json

yarn build

serve -s build
