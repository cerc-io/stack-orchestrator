#!/bin/sh

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

NITRO_ADDRESSES_FILE_PATH="/nitro/nitro-addresses.json"
DESTINATION_FILE_PATH="./src/nitro-addresses.json"

# Check if the file exists
if [ -f "$NITRO_ADDRESSES_FILE_PATH" ]; then
  cat "$NITRO_ADDRESSES_FILE_PATH" > "$DESTINATION_FILE_PATH"
  echo "Nitro addresses set to ${DESTINATION_FILE_PATH}"
else
  echo "File ${NITRO_ADDRESSES_FILE_PATH} does not exist"
  exit 1
fi
