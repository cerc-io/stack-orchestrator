#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------
# Start doublezerod
#
# Optional environment:
#   DOUBLEZERO_RPC_ENDPOINT - Solana RPC endpoint (default: http://127.0.0.1:8899)
#   DOUBLEZERO_ENV          - DoubleZero environment (default: mainnet-beta)
#   DOUBLEZERO_EXTRA_ARGS   - additional doublezerod arguments
# -----------------------------------------------------------------------

RPC_ENDPOINT="${DOUBLEZERO_RPC_ENDPOINT:-http://127.0.0.1:8899}"
DZ_ENV="${DOUBLEZERO_ENV:-mainnet-beta}"

# Ensure state directories exist
mkdir -p /var/lib/doublezerod /var/run/doublezerod

# Generate DZ identity if not already present
DZ_CONFIG_DIR="${HOME}/.config/doublezero"
mkdir -p "$DZ_CONFIG_DIR"
if [ ! -f "$DZ_CONFIG_DIR/id.json" ]; then
  echo "Generating DoubleZero identity..."
  doublezero keygen
fi

echo "Starting doublezerod..."
echo "Environment: $DZ_ENV"
echo "RPC endpoint: $RPC_ENDPOINT"
echo "DZ address: $(doublezero address)"

ARGS=()
[ -n "${DOUBLEZERO_EXTRA_ARGS:-}" ] && read -ra ARGS <<< "$DOUBLEZERO_EXTRA_ARGS"

exec doublezerod \
  -env "$DZ_ENV" \
  -solana-rpc-endpoint "$RPC_ENDPOINT" \
  "${ARGS[@]}"
