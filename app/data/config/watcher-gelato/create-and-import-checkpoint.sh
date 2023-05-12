#!/bin/bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_SNAPSHOT_GQL_ENDPOINT="${CERC_SNAPSHOT_GQL_ENDPOINT:-${DEFAULT_CERC_SNAPSHOT_GQL_ENDPOINT}}"
CERC_SNAPSHOT_BLOCKHASH="${CERC_SNAPSHOT_BLOCKHASH:-${DEFAULT_CERC_SNAPSHOT_BLOCKHASH}}"

# TODO Create a checkpoint using GQL endpoint (check and skip if snapshot file already exists)

echo "Initializing watcher using a state snapshot..."
# TODO Import the checkpoint
