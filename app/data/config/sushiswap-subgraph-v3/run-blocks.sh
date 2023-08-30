#!/bin/bash

set -e

echo "Building blocks subgraph and deploying to graph-node..."

cd blocks

pnpm run generate
pnpm run build

pnpm exec graph create --node http://graph-node:8020/ sushiswap/blocks
pnpm exec graph deploy --node http://graph-node:8020/ --ipfs http://ipfs:5001 --version-label 0.1.0 sushiswap/blocks

echo "Done"
