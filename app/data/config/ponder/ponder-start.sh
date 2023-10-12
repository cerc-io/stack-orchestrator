#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

nitro_addresses_file="/nitro/nitro-addresses.json"
nitro_addresses_destination_file="/app/examples/token-erc20/nitro-addresses.json"

# Check if CERC_NA_ADDRESS environment variable is set
if [ -n "$CERC_NA_ADDRESS" ]; then
  echo "CERC_NA_ADDRESS is set to '$CERC_NA_ADDRESS'"
  echo "CERC_VPA_ADDRESS is set to '$CERC_VPA_ADDRESS'"
  echo "CERC_CA_ADDRESS is set to '$CERC_CA_ADDRESS'"
  echo "Using the above Nitro addresses"

  # Create the required JSON and write it to a file
  nitro_addresses_json=$(jq -n \
    --arg na "$CERC_NA_ADDRESS" \
    --arg vpa "$CERC_VPA_ADDRESS" \
    --arg ca "$CERC_CA_ADDRESS" \
    '.nitroAdjudicatorAddress = $na | .virtualPaymentAppAddress = $vpa | .consensusAppAddress = $ca')
  echo "$nitro_addresses_json" > "${nitro_addresses_destination_file}"
elif [ -f ${nitro_addresses_file} ]; then
  echo "Using Nitro addresses from ${nitro_addresses_file}:"
  cat "$nitro_addresses_file"
  cat "$nitro_addresses_file" > "$nitro_addresses_destination_file"
else
  echo "Nitro addresses not available"
  exit 1
fi

echo "Using CERC_PONDER_NITRO_PK from env for Nitro account"
echo "Using CERC_PONDER_NITRO_CHAIN_PK (account with funds) from env for sending Nitro txs"
echo "Using ${CERC_PONDER_NITRO_CHAIN_URL} as the RPC endpoint for Nitro txs"

# If not set, check the mounted volume for relay peer id
if [ -z "$CERC_RELAY_MULTIADDR" ]; then
  echo "CERC_RELAY_MULTIADDR not provided, taking from the mounted volume"
  CERC_RELAY_MULTIADDR="/dns4/mobymask-watcher-server/tcp/9090/ws/p2p/$(jq -r '.id' /peers/relay-id.json)"
fi

env_file='.env.local'
echo "PONDER_TELEMETRY_DISABLED=true" > "$env_file"
echo "PONDER_LOG_LEVEL=debug" >> "$env_file"
echo "PONDER_CHAIN_ID=\"$CERC_PONDER_CHAIN_ID\"" >> "$env_file"
echo "PONDER_RPC_URL_1=\"$CERC_PONDER_RPC_URL_1\"" >> "$env_file"
echo "PONDER_NITRO_PK=\"$CERC_PONDER_NITRO_PK\"" >> "$env_file"
echo "PONDER_NITRO_CHAIN_PK=\"$CERC_PONDER_NITRO_CHAIN_PK\"" >> "$env_file"
echo "PONDER_NITRO_CHAIN_URL=\"$CERC_PONDER_NITRO_CHAIN_URL\"" >> "$env_file"
echo "RELAY_MULTIADDR=\"$CERC_RELAY_MULTIADDR\"" >> "$env_file"
echo "UPSTREAM_NITRO_ADDRESS=\"$CERC_UPSTREAM_NITRO_ADDRESS\"" >> "$env_file"
echo "UPSTREAM_NITRO_MULTIADDR=\"$CERC_UPSTREAM_NITRO_MULTIADDR\"" >> "$env_file"
echo "UPSTREAM_NITRO_PAY_AMOUNT=\"$CERC_UPSTREAM_NITRO_PAY_AMOUNT\"" >> "$env_file"
echo "INDEXER_GQL_ENDPOINT=\"$CERC_INDEXER_GQL_ENDPOINT\"" >> "$env_file"
echo "INDEXER_NITRO_PAY_AMOUNT=\"$CERC_INDEXER_NITRO_PAY_AMOUNT\"" >> "$env_file"

cat "$env_file"

# Keep the container running
tail -f
