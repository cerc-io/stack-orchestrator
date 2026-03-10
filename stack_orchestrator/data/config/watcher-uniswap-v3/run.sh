#!/bin/sh

set -e
set -u

echo "Initializing watcher..."
yarn fill --start-block $UNISWAP_START_BLOCK --end-block $((UNISWAP_START_BLOCK + 1))

echo "Running active server"
DEBUG=vulcanize:* exec node --enable-source-maps dist/server.js
