#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_L2_GETH_RPC="${CERC_L2_GETH_RPC:-${DEFAULT_CERC_L2_GETH_RPC}}"
CERC_L1_ACCOUNTS_CSV_URL="${CERC_L1_ACCOUNTS_CSV_URL:-${DEFAULT_CERC_L1_ACCOUNTS_CSV_URL}}"

CERC_RELAY_PEERS="${CERC_RELAY_PEERS:-${DEFAULT_CERC_RELAY_PEERS}}"
CERC_DENY_MULTIADDRS="${CERC_DENY_MULTIADDRS:-${DEFAULT_CERC_DENY_MULTIADDRS}}"
CERC_RELAY_ANNOUNCE_DOMAIN="${CERC_RELAY_ANNOUNCE_DOMAIN:-${DEFAULT_CERC_RELAY_ANNOUNCE_DOMAIN}}"
CERC_ENABLE_PEER_L2_TXS="${CERC_ENABLE_PEER_L2_TXS:-${DEFAULT_CERC_ENABLE_PEER_L2_TXS}}"
CERC_DEPLOYED_CONTRACT="${CERC_DEPLOYED_CONTRACT:-${DEFAULT_CERC_DEPLOYED_CONTRACT}}"

echo "Using L2 RPC endpoint ${CERC_L2_GETH_RPC}"

# Use public domain for relay multiaddr in peer config if specified
# Otherwise, use the docker container's host IP
if [ -n "$CERC_RELAY_ANNOUNCE_DOMAIN" ]; then
  CERC_RELAY_MULTIADDR="/dns4/${CERC_RELAY_ANNOUNCE_DOMAIN}/tcp/443/wss/p2p/$(jq -r '.id' /app/peers/relay-id.json)"
else
  CERC_RELAY_MULTIADDR="/dns4/mobymask-watcher-server/tcp/9090/ws/p2p/$(jq -r '.id' /app/peers/relay-id.json)"
fi

# Use contract address from environment variable or set from config.json in mounted volume
if [ -n "$CERC_DEPLOYED_CONTRACT" ]; then
  CONTRACT_ADDRESS="${CERC_DEPLOYED_CONTRACT}"
else
  # Assign deployed contract address from server config (created by mobymask container after deploying contract)
  CONTRACT_ADDRESS=$(jq -r '.address' /server/config.json | tr -d '"')
fi

if [ -n "$CERC_L1_ACCOUNTS_CSV_URL" ] && \
  l1_accounts_response=$(curl -L --write-out '%{http_code}' --silent --output /dev/null "$CERC_L1_ACCOUNTS_CSV_URL") && \
  [ "$l1_accounts_response" -eq 200 ];
then
  echo "Fetching L1 account credentials using provided URL"
  mkdir -p /geth-accounts
  wget -O /geth-accounts/accounts.csv "$CERC_L1_ACCOUNTS_CSV_URL"

  # Read the private key of an L1 account for sending txs from peer
  CERC_PRIVATE_KEY_PEER=$(awk -F, 'NR==2{print $NF}' /geth-accounts/accounts.csv)
else
  echo "Couldn't fetch L1 account credentials, using CERC_PRIVATE_KEY_PEER from env"
fi

# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s|REPLACE_WITH_CERC_RELAY_PEERS|${CERC_RELAY_PEERS}|g; \
          s/REPLACE_WITH_CERC_DENY_MULTIADDRS/${CERC_DENY_MULTIADDRS}/g; \
          s/REPLACE_WITH_CERC_RELAY_ANNOUNCE_DOMAIN/${CERC_RELAY_ANNOUNCE_DOMAIN}/g; \
          s|REPLACE_WITH_CERC_RELAY_MULTIADDR|${CERC_RELAY_MULTIADDR}|g; \
          s/REPLACE_WITH_CERC_ENABLE_PEER_L2_TXS/${CERC_ENABLE_PEER_L2_TXS}/g; \
          s/REPLACE_WITH_CERC_PRIVATE_KEY_PEER/${CERC_PRIVATE_KEY_PEER}/g; \
          s/REPLACE_WITH_CONTRACT_ADDRESS/${CONTRACT_ADDRESS}/g; \
          s|REPLACE_WITH_CERC_L2_GETH_RPC_ENDPOINT|${CERC_L2_GETH_RPC}| ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > environments/local.toml

echo 'yarn server'
yarn server
