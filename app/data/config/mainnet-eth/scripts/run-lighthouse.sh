#!/bin/bash
if [[ "true" == "$CERC_SCRIPT_DEBUG" ]]; then
    set -x
fi

ENR_OPTS=""
if [[ -n "$LIGHTHOUSE_ENR_ADDRESS" ]]; then
  ENR_OPTS="--enr-address $LIGHTHOUSE_ENR_ADDRESS"
fi

exec lighthouse bn \
  --checkpoint-sync-url "$LIGHTHOUSE_CHECKPOINT_SYNC_URL" \
  --checkpoint-sync-url-timeout ${LIGHTHOUSE_CHECKPOINT_SYNC_URL_TIMEOUT} \
  --datadir "$LIGHTHOUSE_DATADIR" \
  --debug-level $LIGHTHOUSE_DEBUG_LEVEL \
  --disable-deposit-contract-sync \
  --disable-upnp \
  --enr-tcp-port $LIGHTHOUSE_NETWORK_PORT \
  --enr-udp-port $LIGHTHOUSE_NETWORK_PORT \
  --execution-endpoint "$LIGHTHOUSE_EXECUTION_ENDPOINT" \
  --execution-jwt /etc/mainnet-eth/jwtsecret \
  --http \
  --http-address 0.0.0.0 \
  --http-port $LIGHTHOUSE_HTTP_PORT \
  --metrics \
  --metrics-address=0.0.0.0 \
  --metrics-port $LIGHTHOUSE_METRICS_PORT \
  --network mainnet \
  --port $LIGHTHOUSE_NETWORK_PORT \
  $ENR_OPTS $LIGHTHOUSE_OPTS
