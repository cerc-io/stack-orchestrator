#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

tail -f /dev/null

# TODO:
# Take urbit endpoint from env
# Check if urbit endpoint is up
# Fire curl requests to create/mount a uniswap desk
# Copy over build to desk data dir
