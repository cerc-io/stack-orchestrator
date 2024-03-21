#!/bin/bash

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

nitro_addresses_file="/app/deployment/nitro-addresses.json"

# Check if CERC_NA_ADDRESS environment variable is set
if [ -n "$CERC_NA_ADDRESS" ]; then
  echo "CERC_NA_ADDRESS is set to '$CERC_NA_ADDRESS'"
  echo "CERC_VPA_ADDRESS is set to '$CERC_VPA_ADDRESS'"
  echo "CERC_CA_ADDRESS is set to '$CERC_CA_ADDRESS'"
  echo "Using the above Nitro addresses"

  NA_ADDRESS=${CERC_NA_ADDRESS}
  VPA_ADDRESS=${CERC_VPA_ADDRESS}
  CA_ADDRESS=${CERC_CA_ADDRESS}
elif [ -f ${nitro_addresses_file} ]; then
  echo "Reading Nitro addresses from ${nitro_addresses_file}"

  NA_ADDRESS=$(jq -r '.nitroAdjudicatorAddress' ${nitro_addresses_file})
  VPA_ADDRESS=$(jq -r '.virtualPaymentAppAddress' ${nitro_addresses_file})
  CA_ADDRESS=$(jq -r '.consensusAppAddress' ${nitro_addresses_file})
else
  echo "File ${nitro_addresses_file} not found"
  exit 1
fi

echo "Running Nitro node"

# Assuming CERC_NITRO_CHAIN_URL is of format <ws|http>://host:port
ws_host=$(echo "$CERC_NITRO_CHAIN_URL" | awk -F '://' '{print $2}' | cut -d ':' -f 1)
ws_port=$(echo "$CERC_NITRO_CHAIN_URL" | awk -F '://' '{print $2}' | cut -d ':' -f 2)

# Wait till chain endpoint is available
retry_interval=5
while true; do
  nc -z -w 1 "$ws_host" "$ws_port"

  if [ $? -eq 0 ]; then
    echo "Chain endpoint is available"
    break
  fi

  echo "Chain endpoint not yet available, retrying in $retry_interval seconds..."
  sleep $retry_interval
done

if [[ -n "$CERC_NITRO_UI_PORT" ]] && [[ -d "/app-node/packages/nitro-gui/dist" ]]; then
  for f in `ls /app-node/packages/nitro-gui/dist/assets/*.js`; do
    sed -i "s#\"CERC_RUNTIME_ENV_RPC_URL\"#\"http://localhost:${CERC_NITRO_RPC_PORT}\"#g" "$f"
    sed -i "s#\"CERC_RUNTIME_ENV_TARGET_URL\"#\"http://localhost:5678\"#g" "$f"
  done
  http-server -p $CERC_NITRO_UI_PORT /app-node/packages/nitro-gui/dist &
fi

if [[ -n "$CERC_NITRO_AUTH_UI_PORT" ]] && [[ -d "/app-node/packages/nitro-auth-gui/dist" ]]; then
  for f in `ls /app-node/packages/nitro-auth-gui/dist/assets/*.js`; do
    sed -i "s#\"CERC_RUNTIME_ENV_RPC_URL\"#\"http://localhost:${CERC_NITRO_RPC_PORT}\"#g" "$f"
    sed -i "s#\"CERC_RUNTIME_ENV_TARGET_URL\"#\"http://localhost:5678\"#g" "$f"
  done
  http-server -p $CERC_NITRO_AUTH_UI_PORT /app-node/packages/nitro-auth-gui/dist &
fi

if [[ "$CERC_NITRO_AUTH_ON" == "true" ]] && [[ -d "/app-node/packages/nitro-auth/dist" ]]; then
  bash -c "sleep 10 && cd /app-node/packages/nitro-auth && yarn start" &
fi

cd /app
./nitro \
  -chainurl ${CERC_NITRO_CHAIN_URL} \
  -msgport ${CERC_NITRO_MSG_PORT} \
  -rpcport ${CERC_NITRO_RPC_PORT} \
  -wsmsgport ${CERC_NITRO_WS_MSG_PORT} \
  -publicip "0.0.0.0" \
  -pk ${CERC_NITRO_PK} \
  -chainpk ${CERC_NITRO_CHAIN_PK} \
  -naaddress ${NA_ADDRESS} \
  -vpaaddress ${VPA_ADDRESS} \
  -caaddress ${CA_ADDRESS} \
  -usedurablestore=${CERC_NITRO_USE_DURABLE_STORE} \
  -durablestorefolder ${CERC_NITRO_DURABLE_STORE_FOLDER} \
  -bootpeers "${CERC_NITRO_BOOT_PEERS}"