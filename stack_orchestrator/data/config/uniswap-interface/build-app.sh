#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

# Check and exit if a deployment already exists (on restarts)
if [ -d /app-builds/uniswap/build ]; then
  echo "Build already exists, remove volume to rebuild"
  exit 0
fi

yarn build

# Copy over build and other files to app-builds for urbit deployment
mkdir -p /app-builds/uniswap
cp -r ./build /app-builds/uniswap/

cp -r mar /app-builds/uniswap/
cp desk.docket-0 /app-builds/uniswap/
