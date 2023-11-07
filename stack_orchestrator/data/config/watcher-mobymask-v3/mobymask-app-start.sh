#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_CHAIN_ID="${CERC_CHAIN_ID:-${DEFAULT_CERC_CHAIN_ID}}"
CERC_DEPLOYED_CONTRACT="${CERC_DEPLOYED_CONTRACT:-${DEFAULT_CERC_DEPLOYED_CONTRACT}}"
CERC_RELAY_NODES="${CERC_RELAY_NODES:-${DEFAULT_CERC_RELAY_NODES}}"
CERC_DENY_MULTIADDRS="${CERC_DENY_MULTIADDRS:-${DEFAULT_CERC_DENY_MULTIADDRS}}"
CERC_PUBSUB="${CERC_PUBSUB:-${DEFAULT_CERC_PUBSUB}}"
CERC_GOSSIPSUB_DIRECT_PEERS="${CERC_GOSSIPSUB_DIRECT_PEERS:-${DEFAULT_CERC_GOSSIPSUB_DIRECT_PEERS}}"
CERC_APP_WATCHER_URL="${CERC_APP_WATCHER_URL:-${DEFAULT_CERC_APP_WATCHER_URL}}"
CERC_SNAP_URL="${CERC_SNAP_URL:-${DEFAULT_CERC_SNAP_URL}}"

# If not set (or []), check the mounted volume for relay peer id
if [ -z "$CERC_RELAY_NODES" ] || [ "$CERC_RELAY_NODES" = "[]" ]; then
  echo "CERC_RELAY_NODES not provided, taking from the mounted volume"
  CERC_RELAY_NODES="[\"/ip4/127.0.0.1/tcp/9090/ws/p2p/$(jq -r '.id' /peers/relay-id.json)\"]"
fi

echo "Using CERC_RELAY_NODES $CERC_RELAY_NODES"

if [ -z "$CERC_DEPLOYED_CONTRACT" ]; then
  # Use config from mounted volume (when running web-app along with watcher stack)
  echo "Taking config for deployed contract from mounted volume"
  while [ ! -f /server/config.json ]; do
    echo "Config not found, retrying in 5 seconds..."
    sleep 5
  done

  # Get deployed contract address and chain id
  CERC_DEPLOYED_CONTRACT=$(jq -r '.address' /server/config.json | tr -d '"')
  CERC_CHAIN_ID=$(jq -r '.chainId' /server/config.json)
else
  echo "Using CERC_DEPLOYED_CONTRACT ${CERC_DEPLOYED_CONTRACT} from env as the MobyMask contract address"
fi

nitro_addresses_file="/nitro/nitro-addresses.json"
nitro_addresses_destination_file="/app/src/utils/nitro-addresses.json"

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

# Export config values in a json file
app_config_file="/app/src/utils/config.json"
app_config_json=$(jq -n \
  --arg name "MobyMask" \
  --argjson enableDebugInfo true \
  --arg address "$CERC_DEPLOYED_CONTRACT" \
  --argjson chainId "$CERC_CHAIN_ID" \
  --argjson relayNodes "$CERC_RELAY_NODES" \
  --argjson denyMultiaddrs "$CERC_DENY_MULTIADDRS" \
  --arg pubsub "$CERC_PUBSUB" \
  --argjson directPeers "$CERC_GOSSIPSUB_DIRECT_PEERS" \
  '.name = $name | .address = $address | .chainId = $chainId | .relayNodes = $relayNodes | .peer.enableDebugInfo = $enableDebugInfo | .peer.denyMultiaddrs = $denyMultiaddrs | .peer.pubsub = $pubsub | .peer.directPeers = $directPeers')
echo "$app_config_json" > "${app_config_file}"

REACT_APP_DEBUG_PEER=true \
REACT_APP_WATCHER_URI="$CERC_APP_WATCHER_URL/graphql" \
REACT_APP_PAY_TO_NITRO_ADDRESS="$CERC_PAYMENT_NITRO_ADDRESS" \
REACT_APP_SNAP_ORIGIN="local:$CERC_SNAP_URL" \
yarn build

http-server -p 80 /app/build
