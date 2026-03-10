#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

pier_dir="/urbit/zod"

# TODO: Bootstrap fake ship on the first run

# Run urbit ship in daemon mode
# Check if the directory exists
if [ -d "$pier_dir" ]; then
  echo "Pier directory already exists, rebooting..."
  /urbit/zod/.run -d
else
  echo "Creating a new fake ship..."
  urbit -d -F zod
fi
