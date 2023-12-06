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

# Move build to app-builds so urbit can deploy it
mkdir -p /app-builds/uniswap
cp -r ./build /app-builds/uniswap/
