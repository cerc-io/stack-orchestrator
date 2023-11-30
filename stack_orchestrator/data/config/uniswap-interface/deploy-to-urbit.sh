#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

tail -f /dev/null

# TODO:
# Wait for glob to exist, copy it over and host it
