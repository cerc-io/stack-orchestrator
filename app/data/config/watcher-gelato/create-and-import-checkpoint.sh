#!/bin/bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_SNAPSHOT_GQL_ENDPOINT="${CERC_SNAPSHOT_GQL_ENDPOINT:-${DEFAULT_CERC_SNAPSHOT_GQL_ENDPOINT}}"
CERC_SNAPSHOT_BLOCKHASH="${CERC_SNAPSHOT_BLOCKHASH:-${DEFAULT_CERC_SNAPSHOT_BLOCKHASH}}"

CHECKPOINT_FILE_PATH="./state_checkpoint/state-gql-${CERC_SNAPSHOT_BLOCKHASH}"

if [ -f "${CHECKPOINT_FILE_PATH}" ]; then
  # Skip checkpoint creation if the file already exists
  echo "File at ${CHECKPOINT_FILE_PATH} already exists, skipping checkpoint creation..."
else
  # Create a checkpoint using GQL endpoint
  echo "Creating a state checkpoint using GQL endpoint..."
  yarn create-state-gql \
    --snapshot-block-hash "${CERC_SNAPSHOT_BLOCKHASH}" \
    --gql-endpoint "${CERC_SNAPSHOT_GQL_ENDPOINT}" \
    --output "${CHECKPOINT_FILE_PATH}"
fi

echo "Initializing watcher using a state snapshot..."

# Import the state checkpoint
# (skips if snapshot block is already indexed)
yarn import-state --import-file "${CHECKPOINT_FILE_PATH}"
