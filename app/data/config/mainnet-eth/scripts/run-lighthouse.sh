#!/bin/bash
if [[ -n "$CERC_SCRIPT_DEBUG" ]]; then
    set -x
fi

ENR_OPTS=""
if [[ -n "$LIGHTHOUSE_ENR_ADDRESS" ]]; then
  ENR_OPTS="--enr-address $LIGHTHOUSE_ENR_ADDRESS"
fi

exec lighthouse bn \
  --checkpoint-sync-url "$LIGHTHOUSE_CHECKPOINT_SYNC_URL" \
  --datadir "$LIGHTHOUSE_DATADIR" \
  --debug-level $LIGHTHOUSE_DEBUG_LEVEL \
  --disable-deposit-contract-sync \
  --enr-tcp-port $LIGHTHOUSE_NETWORK_PORT \
  --enr-udp-port $LIGHTHOUSE_NETWORK_PORT \
  --execution-endpoint "$EXECUTION_ENDPOINT" \
  --execution-jwt /etc/mainnet-eth/jwtsecret \
  --http-address 0.0.0.0 \
  --http-port $LIGHTHOUSE_HTTP_PORT \
  --network mainnet \
  --port $LIGHTHOUSE_NETWORK_PORT \
  $ENR_OPTS $LIGHTHOUSE_OPTS
