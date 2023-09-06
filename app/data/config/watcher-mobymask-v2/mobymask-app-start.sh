#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_CHAIN_ID="${CERC_CHAIN_ID:-${DEFAULT_CERC_CHAIN_ID}}"
CERC_DEPLOYED_CONTRACT="${CERC_DEPLOYED_CONTRACT:-${DEFAULT_CERC_DEPLOYED_CONTRACT}}"
CERC_RELAY_NODES="${CERC_RELAY_NODES:-${DEFAULT_CERC_RELAY_NODES}}"
CERC_DENY_MULTIADDRS="${CERC_DENY_MULTIADDRS:-${DEFAULT_CERC_DENY_MULTIADDRS}}"
CERC_PUBSUB="${CERC_PUBSUB:-${DEFAULT_CERC_PUBSUB}}"
CERC_APP_WATCHER_URL="${CERC_APP_WATCHER_URL:-${DEFAULT_CERC_APP_WATCHER_URL}}"

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
    echo "Config not found, retrying after 5 seconds"
    sleep 5
  done

  # Get deployed contract address and chain id
  CERC_DEPLOYED_CONTRACT=$(jq -r '.address' /server/config.json | tr -d '"')
  CERC_CHAIN_ID=$(jq -r '.chainId' /server/config.json)
else
  echo "Taking deployed contract details from env"
fi

cd /app
git checkout $CERC_RELEASE

# Export config values in a json file
jq --arg address "$CERC_DEPLOYED_CONTRACT" \
  --argjson chainId "$CERC_CHAIN_ID" \
  --argjson relayNodes "$CERC_RELAY_NODES" \
  --argjson denyMultiaddrs "$CERC_DENY_MULTIADDRS" \
  --argjson pubsub "$CERC_PUBSUB" \
  '.address = $address | .chainId = $chainId | .relayNodes = $relayNodes | .peer.denyMultiaddrs = $denyMultiaddrs | .peer.pubsub = $pubsub' \
  /app/src/mobymask-app-config.json > /app/${CERC_CONFIG_FILE}

if [ "${CERC_USE_NPM}" = "true" ]; then
  npm install
  REACT_APP_WATCHER_URI="$CERC_APP_WATCHER_URL/graphql" npm run build
else
  yarn install
  REACT_APP_WATCHER_URI="$CERC_APP_WATCHER_URL/graphql" yarn build
fi

http-server -p 80 /app/build
