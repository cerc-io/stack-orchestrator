#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_L1_RPC="${CERC_L1_RPC:-${DEFAULT_CERC_L1_RPC}}"

# Get Batcher key from keys.json
BATCHER_KEY=$(jq -r '.Batcher.privateKey' /l2-accounts/keys.json | tr -d '"')

cleanup() {
    echo "Signal received, cleaning up..."
    kill ${batcher_pid}

    wait
    echo "Done"
}
trap 'cleanup' INT TERM

# Run op-batcher
op-batcher \
  --l2-eth-rpc=http://op-geth:8545 \
  --rollup-rpc=http://op-node:8547 \
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
  --private-key=$BATCHER_KEY \
  &

batcher_pid=$!
wait $batcher_pid
