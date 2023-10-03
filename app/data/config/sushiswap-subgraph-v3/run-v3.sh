#!/bin/bash

set -e

echo "Building v3 subgraph and deploying to graph-node..."

cd v3

pnpm run generate
pnpm run build

pnpm exec graph create --node http://graph-node:8020/ sushiswap/v3-filecoin
pnpm exec graph deploy --node http://graph-node:8020/ --ipfs http://ipfs:5001 --version-label 0.1.0 sushiswap/v3-filecoin

echo "Done"
