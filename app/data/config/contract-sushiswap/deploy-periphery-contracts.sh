#!/bin/bash

set -e

# Chain config
ETH_RPC_ENDPOINT="${ETH_RPC_ENDPOINT:-${DEFAULT_ETH_RPC_ENDPOINT}}"
CHAIN_ID="${CHAIN_ID:-${DEFAULT_CHAIN_ID}}"
ACCOUNT_PRIVATE_KEY="${ACCOUNT_PRIVATE_KEY:-${DEFAULT_ACCOUNT_PRIVATE_KEY}}"

# Option
DEPLOY="${DEPLOY:-${DEFAULT_DEPLOY}}"

# Create a .env file
echo "ETH_RPC_ENDPOINT=$ETH_RPC_ENDPOINT" > .env
echo "CHAIN_ID=$CHAIN_ID" >> .env
echo "ACCOUNT_PRIVATE_KEY=$ACCOUNT_PRIVATE_KEY" >> .env


echo "Using RPC endpoint $ETH_RPC_ENDPOINT"

# Wait for the RPC endpoint to be up
endpoint=${ETH_RPC_ENDPOINT#http://}
endpoint=${endpoint#https://}
RPC_HOST=$(echo "$endpoint" | awk -F'[:/]' '{print $1}')
RPC_PORT=$(echo "$endpoint" | awk -F'[:/]' '{print $2}')
./wait-for-it.sh -h "${RPC_HOST}" -p "${RPC_PORT}" -s -t 0

if [ "$DEPLOY" ]; then
  # Loop until the factory deployment is detected
  echo "Waiting for core deployments to occur"
  while [ ! -f /app/core-deployments/docker/UniswapV3Factory.json ]; do
    sleep 5
  done

  echo "Reading factory address from core deployments"
  FACTORY_ADDRESS=$(jq -r '.address' /app/core-deployments/docker/UniswapV3Factory.json)

  echo "Using UniswapV3Factory at $FACTORY_ADDRESS"
  echo "FACTORY_ADDRESS=$FACTORY_ADDRESS" >> .env

  echo "Performing periphery contract deployments..."
  yarn hardhat --network docker deploy --tags NonfungiblePositionManager
else
  echo "Skipping contract deployments"
fi

echo "Done"
