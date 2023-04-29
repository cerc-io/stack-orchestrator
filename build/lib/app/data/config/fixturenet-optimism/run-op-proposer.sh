#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_L1_RPC="${CERC_L1_RPC:-${DEFAULT_CERC_L1_RPC}}"

# Read the L2OutputOracle contract address from the deployment
L2OO_DEPLOYMENT=$(cat /contracts-bedrock/deployments/getting-started/L2OutputOracle.json)
L2OO_ADDR=$(echo "$L2OO_DEPLOYMENT" | jq -r '.address')

# Get Proposer key from keys.json
PROPOSER_KEY=$(jq -r '.Proposer.privateKey' /l2-accounts/keys.json | tr -d '"')

cleanup() {
    echo "Signal received, cleaning up..."
    kill ${proposer_pid}

    wait
    echo "Done"
}
trap 'cleanup' INT TERM

# Run op-proposer
op-proposer \
  --poll-interval 12s \
  --rpc.port 8560 \
  --rollup-rpc http://op-node:8547 \
  --l2oo-address $L2OO_ADDR \
  --private-key $PROPOSER_KEY \
  --l1-eth-rpc $CERC_L1_RPC \
  &

proposer_pid=$!
wait $proposer_pid
