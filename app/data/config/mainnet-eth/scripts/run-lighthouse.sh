#!/bin/bash
if [[ -n "$CERC_SCRIPT_DEBUG" ]]; then
    set -x
fi

DEBUG_LEVEL=${CERC_LIGHTHOUSE_DEBUG_LEVEL:-info}

data_dir=/var/lighthouse-data-dir

network_port=9001
http_port=8001
authrpc_port=8551

exec lighthouse \
  bn \
  --debug-level $DEBUG_LEVEL \
  --datadir $data_dir \
  --network mainnet \
  --execution-endpoint $EXECUTION_ENDPOINT \
  --execution-jwt /etc/mainnet-eth/jwtsecret \
  --disable-deposit-contract-sync \
  --checkpoint-sync-url https://mainnet.checkpoint.sigp.io
