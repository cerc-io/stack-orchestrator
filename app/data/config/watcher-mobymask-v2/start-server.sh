#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_L2_GETH_RPC="${CERC_L2_GETH_RPC:-${DEFAULT_CERC_L2_GETH_RPC}}"
CERC_PRIVATE_KEY_PEER="${CERC_PRIVATE_KEY_PEER:-${DEFAULT_CERC_PRIVATE_KEY_PEER}}"

CERC_RELAY_PEERS="${CERC_RELAY_PEERS:-${DEFAULT_CERC_RELAY_PEERS}}"
CERC_RELAY_ANNOUNCE_DOMAIN="${CERC_RELAY_ANNOUNCE_DOMAIN:-${DEFAULT_CERC_RELAY_ANNOUNCE_DOMAIN}}"
CERC_ENABLE_PEER_L2_TXS="${CERC_ENABLE_PEER_L2_TXS:-${DEFAULT_CERC_ENABLE_PEER_L2_TXS}}"
CERC_DEPLOYED_CONTRACT="${CERC_DEPLOYED_CONTRACT:-${DEFAULT_CERC_DEPLOYED_CONTRACT}}"

echo "Using L2 RPC endpoint ${CERC_L2_GETH_RPC}"

# Check for peer ids in ./peers folder, create if not present
if [ -f ./peers/relay-id.json ]; then
  echo "Using peer id for relay node from the mounted volume"
else
  echo "Creating a new peer id for relay node"
  cd ../peer
  yarn create-peer -f ../mobymask-v2-watcher/peers/relay-id.json
  cd ../mobymask-v2-watcher
fi

if [ -f ./peers/peer-id.json ]; then
  echo "Using peer id for peer node from the mounted volume"
else
  echo "Creating a new peer id for peer node"
  cd ../peer
  yarn create-peer -f ../mobymask-v2-watcher/peers/peer-id.json
  cd ../mobymask-v2-watcher
fi

CERC_RELAY_MULTIADDR="/dns4/mobymask-watcher-server/tcp/9090/ws/p2p/$(jq -r '.id' ./peers/relay-id.json)"

# Use contract address from environment variable or set from config.json in mounted volume
if [ -n "$CERC_DEPLOYED_CONTRACT" ]; then
  CONTRACT_ADDRESS="${CERC_DEPLOYED_CONTRACT}"
else
  # Assign deployed contract address from server config (created by mobymask container after deploying contract)
  CONTRACT_ADDRESS=$(jq -r '.address' /server/config.json | tr -d '"')
fi

if [ -f /geth-accounts/accounts.csv ]; then
  echo "Using L1 private key from the mounted volume"
  # Read the private key of L1 account for sending txs from peer
  CERC_PRIVATE_KEY_PEER=$(awk -F, 'NR==2{print $NF}' /geth-accounts/accounts.csv)
else
  echo "Using CERC_PRIVATE_KEY_PEER from env"
fi

# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s/REPLACE_WITH_CERC_RELAY_PEERS/$(echo "${CERC_RELAY_PEERS}" | sed 's/\//\\\//g')/g; \
          s/REPLACE_WITH_CERC_RELAY_ANNOUNCE_DOMAIN/${CERC_RELAY_ANNOUNCE_DOMAIN}/g; \
          s/REPLACE_WITH_CERC_RELAY_MULTIADDR/${CERC_RELAY_MULTIADDR}/g; \
          s/REPLACE_WITH_CERC_ENABLE_PEER_L2_TXS/${CERC_ENABLE_PEER_L2_TXS}/g; \
          s/REPLACE_WITH_CERC_PRIVATE_KEY_PEER/${CERC_PRIVATE_KEY_PEER}/g; \
          s/REPLACE_WITH_CONTRACT_ADDRESS/${CONTRACT_ADDRESS}/g; \
          s|REPLACE_WITH_CERC_L2_GETH_RPC_ENDPOINT|${CERC_L2_GETH_RPC}| ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > environments/local.toml

# Write the relay node's multiaddr to /app/packages/peer/.env for running tests
echo "RELAY=\"$CERC_RELAY_MULTIADDR\"" > /app/packages/peer/.env

echo 'yarn server'
yarn server
