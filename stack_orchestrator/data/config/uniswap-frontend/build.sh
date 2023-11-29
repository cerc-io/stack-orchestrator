#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

yarn build

# Create symlink to host built files with correct URL path
mkdir -p /app/urbit/apps
ln -s /app/build /app/urbit/apps/uniswap

node_modules/.bin/serve urbit -s -l 3000
