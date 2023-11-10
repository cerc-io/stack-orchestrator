#!/bin/sh

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi
set -u

echo "Using RPC query endpoint ${CERC_ETH_RPC_ENDPOINT}"

# Read in the config template TOML file and modify it
# WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG_TEMPLATE=$(cat /home/prathamesh/deepstack/stack-orchestrator/stack_orchestrator/data/config/watcher-sushiswap-v3/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s|REPLACE_WITH_CERC_ETH_RPC_ENDPOINT|${CERC_ETH_RPC_ENDPOINT}| ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > /home/prathamesh/deepstack/stack-orchestrator/stack_orchestrator/data/config/watcher-sushiswap-v3/local.toml


echo "Initializing watcher..."
yarn fill --start-block $SUSHISWAP_START_BLOCK --end-block $((SUSHISWAP_START_BLOCK + 1))

echo "Running server..."
DEBUG=vulcanize:* exec node --enable-source-maps dist/server.js
