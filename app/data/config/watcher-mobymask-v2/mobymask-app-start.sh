#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

# Use config from mounted volume if available (when running web-app along with watcher stack)
if [ -f /server/config.json ]; then
  echo "Merging config for deployed contract from mounted volume"
  # Merging config files to get deployed contract address
  jq -s '.[0] * .[1]' /app/src/mobymask-app-config.json /server/config.json > /app/src/config.json
else
  echo "Setting deployed contract details from env"

  # Set config values from environment variables
  jq --arg address "$DEPLOYED_CONTRACT" \
    --argjson chainId $CHAIN_ID \
    --argjson relayNodes "$RELAY_NODES" \
    '.address = $address | .chainId = $chainId | .relayNodes = $relayNodes' \
    /app/src/mobymask-app-config.json > /app/src/config.json
fi

REACT_APP_WATCHER_URI="$APP_WATCHER_URL/graphql" npm run build

serve -s build
