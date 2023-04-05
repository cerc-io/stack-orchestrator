#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "Using L2 RPC endpoint ${L2_GETH_RPC}"

# Assign deployed contract address from server config
CONTRACT_ADDRESS=$(jq -r '.address' /server/config.json | tr -d '"')

if [ -f /geth-accounts/accounts.csv ]; then
  echo "Using L1 private key from the mounted volume"
  # Read the private key of L1 account for sending txs from peer
  PRIVATE_KEY_PEER=$(awk -F, 'NR==2{print $NF}' /geth-accounts/accounts.csv)
else
  echo "Using PRIVATE_KEY_PEER from env"
fi

sed "s/REPLACE_WITH_PRIVATE_KEY/${PRIVATE_KEY_PEER}/" environments/watcher-config-template.toml > environments/local.toml
sed -i "s/REPLACE_WITH_CONTRACT_ADDRESS/${CONTRACT_ADDRESS}/" environments/local.toml
sed -i 's|REPLACE_WITH_L2_GETH_RPC_ENDPOINT|'"${L2_GETH_RPC}"'|' environments/local.toml

echo 'yarn server'
yarn server
