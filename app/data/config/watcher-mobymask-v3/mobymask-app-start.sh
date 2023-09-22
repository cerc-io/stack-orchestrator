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

echo "Using CERC_RELAY_NODES $CERC_RELAY_NODES"

if [ -z "$CERC_DEPLOYED_CONTRACT" ]; then
  echo "CERC_DEPLOYED_CONTRACT not set"
  exit 1
else
  echo "Using CERC_DEPLOYED_CONTRACT ${CERC_DEPLOYED_CONTRACT} from env as the MobyMask contract address"
fi

# Checkout to the required release/branch
cd /app
git checkout $CERC_RELEASE

# Check if CERC_NA_ADDRESS is set
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
  echo "$nitro_addresses_json" > /app/src/utils/nitro-addresses.json
else
  echo "Nitro addresses not provided"
  exit 1
fi

# Export config values in a json file
jq --arg address "$CERC_DEPLOYED_CONTRACT" \
  --argjson chainId "$CERC_CHAIN_ID" \
  --argjson relayNodes "$CERC_RELAY_NODES" \
  --argjson denyMultiaddrs "$CERC_DENY_MULTIADDRS" \
  --arg pubsub "$CERC_PUBSUB" \
  --argjson directPeers "$CERC_GOSSIPSUB_DIRECT_PEERS" \
  '.address = $address | .chainId = $chainId | .relayNodes = $relayNodes | .peer.denyMultiaddrs = $denyMultiaddrs | .peer.pubsub = $pubsub | .peer.directPeers = $directPeers' \
  /app/src/mobymask-app-config.json > /app/src/utils/config.json

yarn install

REACT_APP_WATCHER_URI="$CERC_APP_WATCHER_URL/graphql" \
REACT_APP_PAY_TO_NITRO_ADDRESS="$CERC_PAYMENT_NITRO_ADDRESS" \
REACT_APP_SNAP_ORIGIN="local:$CERC_SNAP_URL" \
yarn build

http-server -p 80 /app/build
