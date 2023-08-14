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

echo "Using RPC endpoint ${ETH_RPC_ENDPOINT}"

# Wait for the RPC endpoint to be up
endpoint=${ETH_RPC_ENDPOINT#http://}
endpoint=${endpoint#https://}
RPC_HOST=$(echo "$endpoint" | awk -F'[:/]' '{print $1}')
RPC_PORT=$(echo "$endpoint" | awk -F'[:/]' '{print $2}')
./wait-for-it.sh -h "${RPC_HOST}" -p "${RPC_PORT}" -s -t 0

if [ "$DEPLOY" = true ] && [ ! -e "/app/deployments/docker/UniswapV3Factory.json" ]; then
  echo "Performing core contract deployments..."
  pnpm hardhat --network docker deploy --tags UniswapV3Factory
else
  echo "Skipping contract deployments"
fi

echo "Done"
