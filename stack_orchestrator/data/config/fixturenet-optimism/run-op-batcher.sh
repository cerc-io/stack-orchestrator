#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_L1_RPC="${CERC_L1_RPC:-${DEFAULT_CERC_L1_RPC}}"

# Start op-batcher
L2_RPC="http://op-geth:8545"
ROLLUP_RPC="http://op-node:8547"
BATCHER_KEY=$(cat /l2-accounts/accounts.json | jq -r .BatcherKey)

op-batcher \
  --l2-eth-rpc=$L2_RPC \
  --rollup-rpc=$ROLLUP_RPC \
  --poll-interval=1s \
  --sub-safety-margin=6 \
  --num-confirmations=1 \
  --safe-abort-nonce-too-low-count=3 \
  --resubmission-timeout=30s \
  --rpc.addr=0.0.0.0 \
  --rpc.port=8548 \
  --rpc.enable-admin \
  --max-channel-duration=1 \
  --l1-eth-rpc=$CERC_L1_RPC \
  --private-key="${BATCHER_KEY#0x}"
