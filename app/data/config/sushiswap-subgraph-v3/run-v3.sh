#!/bin/bash

set -e

# Loop until the NFPM deployment is detected
# echo "Waiting for sushiswap-periphery deployments to occur"
# while [ ! -f ./deployments/docker/NonfungiblePositionManager.json ]; do
#   sleep 5
# done

# echo "Reading contract addresses and block numbers from deployments"
# FACTORY_ADDRESS=$(jq -r '.address' ./core-deployments/docker/UniswapV3Factory.json)
# FACTORY_BLOCK=$(jq -r '.receipt.blockNumber' ./core-deployments/docker/UniswapV3Factory.json)
# NATIVE_ADDRESS=$(jq -r '.address' ./deployments/docker/WFIL.json)
# NFPM_ADDRESS=$(jq -r '.address' ./deployments/docker/NonfungiblePositionManager.json)
# NFPM_BLOCK=$(jq -r '.receipt.blockNumber' ./deployments/docker/NonfungiblePositionManager.json)

# Read the JavaScript file content
# file_content=$(</app/config/lotus-fixturenet.js.template)

# Replace uppercase words with environment variables
# echo "Reading values in lotus-fixturenet config"
# replaced_content=$(echo "$file_content" | sed -e "s/FACTORY_ADDRESS/$FACTORY_ADDRESS/g" \
#                                               -e "s/FACTORY_BLOCK/$FACTORY_BLOCK/g" \
#                                               -e "s/NFPM_ADDRESS/$NFPM_ADDRESS/g" \
#                                               -e "s/NFPM_BLOCK/$NFPM_BLOCK/g" \
#                                               -e "s/NATIVE_ADDRESS/$NATIVE_ADDRESS/g")

# Write the replaced content back to the JavaScript file
# echo "$replaced_content" > /app/config/lotus-fixturenet.js

echo "Building v3 subgraph and deploying to graph-node..."

cd v3

pnpm run generate
pnpm run build

# pnpm exec graph create --node http://graph-node:8020/ sushiswap/v3-lotus
# pnpm exec graph deploy --node http://graph-node:8020/ --ipfs http://ipfs:5001 --version-label 0.1.0 sushiswap/v3-lotus
pnpm exec graph create --node http://graph-node:8020/ sushiswap/v3-filecoin
pnpm exec graph deploy --node http://graph-node:8020/ --ipfs http://ipfs:5001 --version-label 0.1.0 sushiswap/v3-filecoin

echo "Done"
