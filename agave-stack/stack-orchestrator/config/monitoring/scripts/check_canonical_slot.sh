#!/bin/bash
# Query canonical mainnet slot for sync lag comparison

set -euo pipefail

CANONICAL_RPC="${CANONICAL_RPC_URL:-https://api.mainnet-beta.solana.com}"

response=$(curl -s --max-time 10 -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getSlot"}' \
  "$CANONICAL_RPC" 2>/dev/null || echo '{"result":0}')

slot=$(echo "$response" | grep -o '"result":[0-9]*' | grep -o '[0-9]*' || echo "0")

if [ "$slot" != "0" ]; then
  echo "canonical_slot slot=${slot}i"
fi
