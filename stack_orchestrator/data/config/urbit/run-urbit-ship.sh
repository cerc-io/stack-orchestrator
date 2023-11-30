#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

pier_dir="/urbit/zod"

# Run urbit ship in daemon mode
# Check if the directory exists
if [ -d "$pier_dir" ]; then
  echo "Pier directory already exists, rebooting..."
  urbit -d zod
else
  echo "Creating a new fake ship..."
  urbit -d -F zod
fi
