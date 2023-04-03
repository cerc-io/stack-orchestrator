#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

export L1_RPC="http://${L1_HOST}:${L1_PORT}"

op-node genesis l2 \
  --deploy-config /contracts-bedrock/deploy-config/getting-started.json \
  --deployment-dir /contracts-bedrock/deployments/getting-started/ \
  --outfile.l2 /app/genesis.json \
  --outfile.rollup /app/rollup.json \
  --l1-rpc $L1_RPC

openssl rand -hex 32 > /app/jwt.txt
