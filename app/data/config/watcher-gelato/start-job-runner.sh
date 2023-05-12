#!/bin/bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_ETH_SERVER_GQL_ENDPOINT="${CERC_ETH_SERVER_GQL_ENDPOINT:-${DEFAULT_CERC_ETH_SERVER_GQL_ENDPOINT}}"
CERC_ETH_SERVER_RPC_ENDPOINT="${CERC_ETH_SERVER_RPC_ENDPOINT:-${DEFAULT_CERC_ETH_SERVER_RPC_ENDPOINT}}"

echo "Using ETH server GQL endpoint ${CERC_ETH_SERVER_GQL_ENDPOINT}"
echo "Using ETH server RPC endpoint ${CERC_ETH_SERVER_RPC_ENDPOINT}"

# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s|REPLACE_WITH_ETH_SERVER_GQL_ENDPOINT|${CERC_ETH_SERVER_GQL_ENDPOINT}|g; \
          s|REPLACE_WITH_ETH_SERVER_RPC_ENDPOINT|${CERC_ETH_SERVER_RPC_ENDPOINT}| ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > environments/local.toml

echo "Running job-runner"
DEBUG=vulcanize:* exec node --enable-source-maps dist/job-runner.js
