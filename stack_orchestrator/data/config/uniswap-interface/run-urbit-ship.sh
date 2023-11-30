#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

pier_dir="/urbit/zod"

# Check if the directory exists
if [ -d "$pier_dir" ]; then
  echo "Pier directory already exists, rebooting..."
  urbit -t zod
else
  echo "Creating a new fake ship..."
  urbit -t -F zod
fi
