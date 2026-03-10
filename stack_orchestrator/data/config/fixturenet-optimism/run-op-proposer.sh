#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_L1_RPC="${CERC_L1_RPC:-${DEFAULT_CERC_L1_RPC}}"
CERC_L1_CHAIN_ID="${CERC_L1_CHAIN_ID:-${DEFAULT_CERC_L1_CHAIN_ID}}"
DEPLOYMENT_CONTEXT="$CERC_L1_CHAIN_ID"

# Start op-proposer
ROLLUP_RPC="http://op-node:8547"
PROPOSER_KEY=$(cat /l2-accounts/accounts.json | jq -r .ProposerKey)
L2OO_ADDR=$(cat /l1-deployment/$DEPLOYMENT_CONTEXT/L2OutputOracleProxy.json | jq -r .address)

op-proposer \
  --poll-interval=12s \
  --rpc.port=8560 \
  --rollup-rpc=$ROLLUP_RPC \
  --l2oo-address="${L2OO_ADDR#0x}" \
  --private-key="${PROPOSER_KEY#0x}" \
  --l1-eth-rpc=$CERC_L1_RPC
