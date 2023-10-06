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

# Wait till chain endpoint is available
retry_interval=5
while true; do
  # Assuming CERC_NITRO_CHAIN_URL is of format <ws|http>://host:port
  ws_host=$(echo "$CERC_NITRO_CHAIN_URL" | awk -F '://' '{print $2}' | cut -d ':' -f 1)
  ws_port=$(echo "$CERC_NITRO_CHAIN_URL" | awk -F '://' '{print $2}' | cut -d ':' -f 2)
  nc -z -w 1 "$ws_host" "$ws_port"

  if [ $? -eq 0 ]; then
    echo "Chain endpoint is available"
    break
  fi

  echo "Chain endpoint not yet available, retrying in $retry_interval seconds..."
  sleep $retry_interval
done

./nitro -chainurl ${CERC_NITRO_CHAIN_URL} -msgport 3005 -rpcport 4005 -wsmsgport 5005 -pk ${CERC_NITRO_PK} -chainpk ${CERC_NITRO_CHAIN_PK} -naaddress ${NA_ADDRESS} -vpaaddress ${VPA_ADDRESS} -caaddress ${CA_ADDRESS} -usedurablestore ${CERC_NITRO_USE_DURABLE_STORE} -durablestorefolder ${CERC_NITRO_DURABLE_STORE_FOLDER}
