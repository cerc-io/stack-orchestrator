#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

# Use config from mounted volume (when running web-app along with watcher stack)
echo "Waiting for uniswap app glob"
while [ ! -d /app-globs/uniswap ]; do
  echo "Glob directory not found, retrying in 5 seconds..."
  sleep 5
done


# Copy to a new globs directory
mkdir -p globs
cp -r /app-globs/uniswap/* ./globs

# Serve the glob file
cd globs
python3 -m http.server 3000 --bind 0.0.0.0
