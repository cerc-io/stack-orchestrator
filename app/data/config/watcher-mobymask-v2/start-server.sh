#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "Using L2 RPC endpoint ${L2_GETH_RPC}"

# Use contract address from environment variable or set from config.json in mounted volume
if [ -n "$DEPLOYED_CONTRACT" ]; then
  CONTRACT_ADDRESS="${DEPLOYED_CONTRACT}"
else
  # Assign deployed contract address from server config (created by mobymask container after deploying contract)
  CONTRACT_ADDRESS=$(jq -r '.address' /server/config.json | tr -d '"')
fi

if [ -f /geth-accounts/accounts.csv ]; then
  echo "Using L1 private key from the mounted volume"
  # Read the private key of L1 account for sending txs from peer
  PRIVATE_KEY_PEER=$(awk -F, 'NR==2{print $NF}' /geth-accounts/accounts.csv)
else
  echo "Using PRIVATE_KEY_PEER from env"
fi


# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s/REPLACE_WITH_ENABLE_PEER_L2_TXS/${ENABLE_PEER_L2_TXS}/g; \
          s/REPLACE_WITH_PRIVATE_KEY_PEER/${PRIVATE_KEY_PEER}/g; \
          s/REPLACE_WITH_CONTRACT_ADDRESS/${CONTRACT_ADDRESS}/g; \
          s|REPLACE_WITH_L2_GETH_RPC_ENDPOINT|${L2_GETH_RPC}| ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > environments/local.toml

echo 'yarn server'
yarn server
