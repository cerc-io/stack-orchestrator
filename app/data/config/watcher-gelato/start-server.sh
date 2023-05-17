#!/bin/bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_IPLD_ETH_RPC="${CERC_IPLD_ETH_RPC:-${DEFAULT_CERC_IPLD_ETH_RPC}}"
CERC_IPLD_ETH_GQL="${CERC_IPLD_ETH_GQL:-${DEFAULT_CERC_IPLD_ETH_GQL}}"

CERC_USE_STATE_SNAPSHOT="${CERC_USE_STATE_SNAPSHOT:-${DEFAULT_CERC_USE_STATE_SNAPSHOT}}"

echo "Using ETH server RPC endpoint ${CERC_IPLD_ETH_RPC}"
echo "Using ETH server GQL endpoint ${CERC_IPLD_ETH_GQL}"

# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s|REPLACE_WITH_CERC_IPLD_ETH_GQL|${CERC_IPLD_ETH_GQL}|g; \
          s|REPLACE_WITH_CERC_IPLD_ETH_RPC|${CERC_IPLD_ETH_RPC}| ")

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
