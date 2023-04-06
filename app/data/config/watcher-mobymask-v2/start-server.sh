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

# Set private key and contract address for watcher peer txs to L2 only if PRIVATE_KEY_PEER variable is set
if [ -n "$PRIVATE_KEY_PEER" ]; then
  # Read in config template TOML file and modify it
  CONTENT=$(cat environments/watcher-config-template.toml)
  NEW_CONTENT=$(echo "$CONTENT" | sed -E "/\[metrics\]/i \\\n\n      [server.p2p.peer.l2TxConfig]\n        privateKey = \"${PRIVATE_KEY_PEER}\"\n        contractAddress = \"${CONTRACT_ADDRESS}\"\n")

  # Write the modified content to a watcher config file
  echo "$NEW_CONTENT" > environments/local.toml

  sed -i 's|REPLACE_WITH_L2_GETH_RPC_ENDPOINT|'"${L2_GETH_RPC}"'|' environments/local.toml
else
  # Copy template config to watcher config without setting params for peer L2 txs
  cp environments/watcher-config-template.toml environments/local.toml
fi

echo 'yarn server'
yarn server
