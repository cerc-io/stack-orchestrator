#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_L1_RPC="${CERC_L1_RPC:-${DEFAULT_CERC_L1_RPC}}"

# Get Sequencer key from keys.json
SEQUENCER_KEY=$(jq -r '.Sequencer.privateKey' /l2-accounts/keys.json | tr -d '"')

# Run op-node
op-node \
  --l2=http://op-geth:8551 \
  --l2.jwt-secret=/op-node-data/jwt.txt \
  --sequencer.enabled \
  --sequencer.l1-confs=3 \
  --verifier.l1-confs=3 \
  --rollup.config=/op-node-data/rollup.json \
  --rpc.addr=0.0.0.0 \
  --rpc.port=8547 \
  --p2p.disable \
  --rpc.enable-admin \
  --p2p.sequencer.key=$SEQUENCER_KEY \
  --l1=$CERC_L1_RPC \
  --l1.rpckind=any
