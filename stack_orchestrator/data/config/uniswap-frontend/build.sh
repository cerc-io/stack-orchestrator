#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

yarn build

# Create symlink to host built files with correct URL path
mkdir ./urbit/apps
ln -s ./build/ ./urbit/apps/uniswap

yarn serve build -s -l 3000
