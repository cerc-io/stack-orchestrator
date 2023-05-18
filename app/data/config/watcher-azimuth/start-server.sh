#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_IPLD_ETH_RPC="${CERC_IPLD_ETH_RPC:-${DEFAULT_CERC_IPLD_ETH_RPC}}"
CERC_IPLD_ETH_GQL="${CERC_IPLD_ETH_GQL:-${DEFAULT_CERC_IPLD_ETH_GQL}}"

echo "Using IPLD ETH RPC endpoint ${CERC_IPLD_ETH_RPC}"
echo "Using IPLD GQL endpoint ${CERC_IPLD_ETH_GQL}"

# Replace env variables in template TOML file
# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s|REPLACE_WITH_CERC_IPLD_ETH_RPC|${CERC_IPLD_ETH_RPC}|g; \
          s|REPLACE_WITH_CERC_IPLD_ETH_GQL|${CERC_IPLD_ETH_GQL}| ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > environments/watcher-config.toml

# Merge SO watcher config with existing config file
node merge-toml.js

echo 'yarn server'
yarn server
