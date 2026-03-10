#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "Using ETH RPC endpoints ${CERC_ETH_RPC_ENDPOINTS}"
echo "Using IPLD GQL endpoint ${CERC_IPLD_ETH_GQL_ENDPOINT}"
echo "Using historicalLogsBlockRange ${CERC_HISTORICAL_BLOCK_RANGE:-2000}"

# Convert the comma-separated list in CERC_ETH_RPC_ENDPOINTS to a JSON array
RPC_ENDPOINTS_ARRAY=$(echo "$CERC_ETH_RPC_ENDPOINTS" | tr ',' '\n' | awk '{print "\"" $0 "\""}' | paste -sd, - | sed 's/^/[/; s/$/]/')

# Replace env variables in template TOML file
# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s|REPLACE_WITH_CERC_ETH_RPC_ENDPOINTS|${RPC_ENDPOINTS_ARRAY}|g; \
          s|REPLACE_WITH_CERC_IPLD_ETH_GQL_ENDPOINT|${CERC_IPLD_ETH_GQL_ENDPOINT}|g; \
          s|REPLACE_WITH_CERC_HISTORICAL_BLOCK_RANGE|${CERC_HISTORICAL_BLOCK_RANGE:-2000}| ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > environments/watcher-config.toml

# Merge SO watcher config with existing config file
node merge-toml.js

yarn watch:contract --address $CONTRACT_ADDRESS --kind $CONTRACT_NAME --checkpoint true --starting-block $STARTING_BLOCK

echo 'yarn job-runner'
yarn job-runner
