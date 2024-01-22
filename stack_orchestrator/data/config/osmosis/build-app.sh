#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

# Check and exit if a deployment already exists (on restarts)
if [ -d /app-builds/osmosis/build ]; then
  echo "Build already exists, remove volume to rebuild"
  exit 0
fi

yarn build:static

# Move build to app-builds
mkdir -p /app-builds/osmosis
cp -r ./out /app-builds/osmosis/build
