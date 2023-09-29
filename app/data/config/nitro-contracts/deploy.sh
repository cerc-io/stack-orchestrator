#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

nitro_addresses_file="/app/deployment/nitro-addresses.json"

# Check if CERC_NA_ADDRESS environment variable set to skip contract deployment
if [ -n "$CERC_NA_ADDRESS" ]; then
  echo "CERC_NA_ADDRESS is set to '$CERC_NA_ADDRESS'"
  echo "CERC_VPA_ADDRESS is set to '$CERC_VPA_ADDRESS'"
  echo "CERC_CA_ADDRESS is set to '$CERC_CA_ADDRESS'"
  echo "Skipping Nitro contracts deployment"
  exit
fi

# Check and exit if a deployment already exists (on restarts)
if [ -f ${nitro_addresses_file} ]; then
  echo "${nitro_addresses_file} already exists, skipping Nitro contracts deployment"
  cat ${nitro_addresses_file}
  exit
fi

echo "Using ETH RPC endpoint ${CERC_ETH_RPC_ENDPOINT}"

# Wait till ETH RPC endpoint is available with block number > 1
retry_interval=5
while true; do
  block_number_hex=$(curl -s -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' ${CERC_ETH_RPC_ENDPOINT} | jq -r '.result')

  # Check if the request call was successful
  if [ $? -ne 0 ]; then
    echo "RPC endpoint not yet available, retrying in $retry_interval seconds..."
    sleep $retry_interval
    continue
  fi

  # Convert hex to decimal
  block_number_dec=$(printf %u ${block_number_hex})

  # Check if block number is > 1 to avoid failures in the deployment
  if [ "$block_number_dec" -ge 1 ]; then
    echo "RPC endpoint is up"
    break
  else
    echo "RPC endpoint not yet available, retrying in $retry_interval seconds..."
    sleep $retry_interval
    continue
  fi
done

# TODO: Fetch pk from ACCOUNTS_CSV_URL?
echo "Using CERC_PRIVATE_KEY_DEPLOYER from env"

yarn test:deploy-contracts --chainurl ${CERC_ETH_RPC_ENDPOINT} --key ${CERC_PRIVATE_KEY_DEPLOYER} --addressesFilePath ${nitro_addresses_file}
cat ${nitro_addresses_file}
