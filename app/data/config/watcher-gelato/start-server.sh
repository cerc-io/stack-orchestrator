#!/bin/bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_ETH_SERVER_GQL_ENDPOINT="${CERC_ETH_SERVER_GQL_ENDPOINT:-${DEFAULT_CERC_ETH_SERVER_GQL_ENDPOINT}}"
CERC_ETH_SERVER_RPC_ENDPOINT="${CERC_ETH_SERVER_RPC_ENDPOINT:-${DEFAULT_CERC_ETH_SERVER_RPC_ENDPOINT}}"

CERC_USE_STATE_SNAPSHOT="${CERC_USE_STATE_SNAPSHOT:-${DEFAULT_CERC_USE_STATE_SNAPSHOT}}"

echo "Using ETH server GQL endpoint ${CERC_ETH_SERVER_GQL_ENDPOINT}"
echo "Using ETH server RPC endpoint ${CERC_ETH_SERVER_RPC_ENDPOINT}"

# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s|REPLACE_WITH_ETH_SERVER_GQL_ENDPOINT|${CERC_ETH_SERVER_GQL_ENDPOINT}|g; \
          s|REPLACE_WITH_ETH_SERVER_RPC_ENDPOINT|${CERC_ETH_SERVER_RPC_ENDPOINT}| ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > environments/local.toml

if [ "$CERC_USE_STATE_SNAPSHOT" = true ] ; then
  ./create-and-import-checkpoint.sh
else
  echo "Initializing watcher using fill..."
  yarn fill --start-block $DEFAULT_CERC_GELATO_START_BLOCK --end-block $DEFAULT_CERC_GELATO_START_BLOCK
fi

echo "Running active server"
DEBUG=vulcanize:* exec node --enable-source-maps dist/server.js
