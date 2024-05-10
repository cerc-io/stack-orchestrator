#!/bin/sh

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi
set -u

echo "Using ETH RPC endpoints ${CERC_ETH_RPC_ENDPOINTS}"

# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)

# Convert the comma-separated list in CERC_ETH_RPC_ENDPOINTS to a JSON array
RPC_ENDPOINTS_ARRAY=$(echo "$CERC_ETH_RPC_ENDPOINTS" | tr ',' '\n' | awk '{print "\"" $0 "\""}' | paste -sd, - | sed 's/^/[/; s/$/]/')

WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s|REPLACE_WITH_CERC_ETH_RPC_ENDPOINTS|${RPC_ENDPOINTS_ARRAY}| ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > environments/local.toml

echo "Running job-runner..."
DEBUG=vulcanize:* exec node --enable-source-maps dist/job-runner.js
