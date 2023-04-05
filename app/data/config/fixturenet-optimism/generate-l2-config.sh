#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

# Check existing config if it exists
if [ -f /app/jwt.txt ] && [ -f /app/rollup.json ]; then
  echo "Found existing L2 config, cross-checking with L1 deployment config"

  SOURCE_L1_CONF=$(cat /contracts-bedrock/deploy-config/getting-started.json)
  EXP_L1_BLOCKHASH=$(echo "$SOURCE_L1_CONF" | jq -r '.l1StartingBlockTag')
  EXP_BATCHER=$(echo "$SOURCE_L1_CONF" | jq -r '.batchSenderAddress')

  GEN_L2_CONF=$(cat /app/rollup.json)
  GEN_L1_BLOCKHASH=$(echo "$GEN_L2_CONF" | jq -r '.genesis.l1.hash')
  GEN_BATCHER=$(echo "$GEN_L2_CONF" | jq -r '.genesis.system_config.batcherAddr')

  if [ "$EXP_L1_BLOCKHASH" = "$GEN_L1_BLOCKHASH" ] && [ "$EXP_BATCHER" = "$GEN_BATCHER" ]; then
    echo "Config cross-checked, exiting"
    exit 0
  fi

  echo "Existing L2 config doesn't match the L1 deployment config, please clear L2 config volume before starting"
  exit 1
fi

op-node genesis l2 \
  --deploy-config /contracts-bedrock/deploy-config/getting-started.json \
  --deployment-dir /contracts-bedrock/deployments/getting-started/ \
  --outfile.l2 /app/genesis.json \
  --outfile.rollup /app/rollup.json \
  --l1-rpc $L1_RPC

openssl rand -hex 32 > /app/jwt.txt
