#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

watcher_keys_dir="/server/keys"

# Configure relay nodes to connect to
# Note: Assuming host ports for watchers (1-3) relay nodes
RELAY_NODES="[\"/ip4/127.0.0.1/tcp/9090/ws/p2p/$(jq -r '.relayPeerId.id' ${watcher_keys_dir}/watcher-1.json)\", \"/ip4/127.0.0.1/tcp/9091/ws/p2p/$(jq -r '.relayPeerId.id' ${watcher_keys_dir}/watcher-2.json)\", \"/ip4/127.0.0.1/tcp/9092/ws/p2p/$(jq -r '.relayPeerId.id' ${watcher_keys_dir}/watcher-3.json)\"]"

# Configure watcher (1) Nitro account to make payments to
PAYMENT_NITRO_ADDRESS=$(jq -r '.peer.nitroAddress' ${watcher_keys_dir}/watcher-1.json)

echo "Using RELAY_NODES $RELAY_NODES"
echo "Using PAYMENT_NITRO_ADDRESS $PAYMENT_NITRO_ADDRESS"

# Use config from mounted volume
echo "Taking config for deployed contracts from mounted volume"
while [ ! -f /server/config.json ]; do
  echo "Config not found, retrying in 5 seconds..."
  sleep 5
done

# Get deployed contract address and chain id
DEPLOYED_CONTRACT=$(jq -r '.address' /server/config.json | tr -d '"')
CHAIN_ID=$(jq -r '.chainId' /server/config.json)

echo "Using DEPLOYED_CONTRACT $DEPLOYED_CONTRACT"
echo "Using CHAIN_ID $CHAIN_ID"

nitro_addresses_file="/nitro/nitro-addresses.json"
nitro_addresses_destination_file="/app/src/utils/nitro-addresses.json"
if [ -f ${nitro_addresses_file} ]; then
  echo "Using Nitro addresses from ${nitro_addresses_file}:"
  cat "$nitro_addresses_file"
  cat "$nitro_addresses_file" > "$nitro_addresses_destination_file"
else
  echo "Nitro addresses not available"
  exit 1
fi

# Export config values in a json file
app_config_file="/app/src/utils/config.json"
app_config_json=$(jq -n \
  --arg name "MobyMask" \
  --argjson enableDebugInfo true \
  --arg address "$DEPLOYED_CONTRACT" \
  --argjson chainId "$CHAIN_ID" \
  --argjson relayNodes "$RELAY_NODES" \
  --argjson denyMultiaddrs "[]" \
  --arg pubsub "" \
  --argjson directPeers "[]" \
  '.name = $name | .address = $address | .chainId = $chainId | .relayNodes = $relayNodes | .peer.enableDebugInfo = $enableDebugInfo | .peer.denyMultiaddrs = $denyMultiaddrs | .peer.pubsub = $pubsub | .peer.directPeers = $directPeers')
echo "$app_config_json" > "${app_config_file}"

echo "Using CERC_APP_WATCHER_URL $CERC_APP_WATCHER_URL"
echo "Using CERC_SNAP_URL $CERC_SNAP_URL"

REACT_APP_DEBUG_PEER=true \
REACT_APP_WATCHER_URI="$CERC_APP_WATCHER_URL/graphql" \
REACT_APP_PAY_TO_NITRO_ADDRESS="$PAYMENT_NITRO_ADDRESS" \
REACT_APP_SNAP_ORIGIN="local:$CERC_SNAP_URL" \
yarn build

http-server -p 80 /app/build
