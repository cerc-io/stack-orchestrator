#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

erc20_address_file="/app/deployment/erc20-address.json"

echo ETH_RPC_URL=${CERC_ETH_RPC_ENDPOINT} > .env
echo ACCOUNT_PRIVATE_KEY=${CERC_PRIVATE_KEY_DEPLOYER} >> .env

# Check and keep container running if a deployment already exists (on restarts)
if [ -f ${erc20_address_file} ]; then
  echo "${erc20_address_file} already exists, skipping ERC20 contract deployment"
  cat ${erc20_address_file}

  # Keep the container running
  tail -f
fi

wait_for_chain_endpoint() {
  # Wait till ETH RPC endpoint is available with block number > 1
  retry_interval=5
  while true; do
    block_number_hex=$(curl -s -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' ${CERC_ETH_RPC_ENDPOINT} | jq -r '.result')

    # Check if the request call was successful
    if [ $? -ne 0 ]; then
      echo "RPC endpoint ${CERC_ETH_RPC_ENDPOINT} not yet available, retrying in $retry_interval seconds..."
      sleep $retry_interval
      continue
    fi

    # Convert hex to decimal
    block_number_dec=$(printf %u ${block_number_hex})

    # Check if block number is > 1 to avoid failures in the deployment
    if [ "$block_number_dec" -ge 1 ]; then
      echo "RPC endpoint ${CERC_ETH_RPC_ENDPOINT} is up"
      break
    else
      echo "RPC endpoint ${CERC_ETH_RPC_ENDPOINT} not yet available, retrying in $retry_interval seconds..."
      sleep $retry_interval
      continue
    fi
  done
}

wait_for_chain_endpoint

echo "Using CERC_PRIVATE_KEY_DEPLOYER from env"

yarn token:deploy:docker --file ${erc20_address_file}

# Keep the container running
tail -f
