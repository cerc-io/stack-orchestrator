#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_L2_GETH_RPC="${CERC_L2_GETH_RPC:-${DEFAULT_CERC_L2_GETH_RPC}}"

CERC_RELAY_PEERS="${CERC_RELAY_PEERS:-${DEFAULT_CERC_RELAY_PEERS}}"
CERC_DENY_MULTIADDRS="${CERC_DENY_MULTIADDRS:-${DEFAULT_CERC_DENY_MULTIADDRS}}"
CERC_PUBSUB="${CERC_PUBSUB:-${DEFAULT_CERC_PUBSUB}}"
CERC_RELAY_ANNOUNCE_DOMAIN="${CERC_RELAY_ANNOUNCE_DOMAIN:-${DEFAULT_CERC_RELAY_ANNOUNCE_DOMAIN}}"
CERC_ENABLE_PEER_L2_TXS="${CERC_ENABLE_PEER_L2_TXS:-${DEFAULT_CERC_ENABLE_PEER_L2_TXS}}"
CERC_DEPLOYED_CONTRACT="${CERC_DEPLOYED_CONTRACT:-${DEFAULT_CERC_DEPLOYED_CONTRACT}}"

nitro_addresses_file="/nitro/nitro-addresses.json"
nitro_addresses_destination_file="./src/nitro-addresses.json"

watcher_keys_dir="./keys"

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

# Copy the deployed Nitro addresses to the required path
if [ -f "$nitro_addresses_file" ]; then
  cat "$nitro_addresses_file" > "$nitro_addresses_destination_file"
  echo "Nitro addresses set to ${nitro_addresses_destination_file}"

  # Build after setting the Nitro addresses
  yarn build
else
  echo "File ${nitro_addresses_file} does not exist"
  exit 1
fi

echo "Using CERC_PRIVATE_KEY_PEER (account with funds) from env for sending txs to L2"
echo "Using CERC_PRIVATE_KEY_NITRO from env for Nitro account"

# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s|REPLACE_WITH_CERC_RELAY_PEERS|${CERC_RELAY_PEERS}|g; \
          s|REPLACE_WITH_CERC_DENY_MULTIADDRS|${CERC_DENY_MULTIADDRS}|g; \
          s/REPLACE_WITH_CERC_PUBSUB/${CERC_PUBSUB}/g; \
          s/REPLACE_WITH_CERC_RELAY_ANNOUNCE_DOMAIN/${CERC_RELAY_ANNOUNCE_DOMAIN}/g; \
          s|REPLACE_WITH_CERC_RELAY_MULTIADDR|${CERC_RELAY_MULTIADDR}|g; \
          s/REPLACE_WITH_CERC_ENABLE_PEER_L2_TXS/${CERC_ENABLE_PEER_L2_TXS}/g; \
          s/REPLACE_WITH_CERC_PRIVATE_KEY_PEER/${CERC_PRIVATE_KEY_PEER}/g; \
          s/REPLACE_WITH_CERC_PRIVATE_KEY_NITRO/${CERC_PRIVATE_KEY_NITRO}/g; \
          s/REPLACE_WITH_CONTRACT_ADDRESS/${CONTRACT_ADDRESS}/g; \
          s|REPLACE_WITH_CERC_L2_GETH_RPC_ENDPOINT|${CERC_L2_GETH_RPC}| ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > environments/local.toml

echo 'yarn server'
yarn server
