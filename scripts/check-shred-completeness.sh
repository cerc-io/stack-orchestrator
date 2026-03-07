#!/bin/bash
# Check shred completeness at the tip of the blockstore.
#
# Samples the most recent N slots and reports how many are full.
# Use this to determine when enough complete blocks have accumulated
# to safely download a new snapshot that lands within the complete range.
#
# Usage: kubectl exec ... -- bash -c "$(cat check-shred-completeness.sh)"
#   Or:  ssh biscayne ... 'KUBECONFIG=... kubectl exec ... -- agave-ledger-tool ...'

set -euo pipefail

KUBECONFIG="${KUBECONFIG:-/home/rix/.kube/config}"
NS="laconic-laconic-70ce4c4b47e23b85"
DEPLOY="laconic-70ce4c4b47e23b85-deployment"
SAMPLE_SIZE="${1:-200}"

# Get blockstore bounds
BOUNDS=$(kubectl exec -n "$NS" deployment/"$DEPLOY" -c agave-validator -- \
    agave-ledger-tool -l /data/ledger blockstore bounds 2>&1 | grep "^Ledger")

HIGHEST=$(echo "$BOUNDS" | grep -oP 'to \K[0-9]+')
START=$((HIGHEST - SAMPLE_SIZE))

echo "Blockstore highest slot: $HIGHEST"
echo "Sampling slots $START to $HIGHEST ($SAMPLE_SIZE slots)"
echo ""

# Get slot metadata
OUTPUT=$(kubectl exec -n "$NS" deployment/"$DEPLOY" -c agave-validator -- \
    agave-ledger-tool -l /data/ledger blockstore print \
    --starting-slot "$START" --ending-slot "$HIGHEST" 2>&1 \
    | grep -E "^Slot|is_full")

TOTAL=$(echo "$OUTPUT" | grep -c "^Slot" || true)
FULL=$(echo "$OUTPUT" | grep -c "is_full: true" || true)
INCOMPLETE=$(echo "$OUTPUT" | grep -c "is_full: false" || true)

echo "Total slots with data: $TOTAL / $SAMPLE_SIZE"
echo "Complete (is_full: true): $FULL"
echo "Incomplete (is_full: false): $INCOMPLETE"

if [ "$TOTAL" -gt 0 ]; then
    PCT=$((FULL * 100 / TOTAL))
    echo "Completeness: ${PCT}%"
else
    echo "Completeness: N/A (no data)"
fi

echo ""

# Find the first full slot counting backward from the tip
# This tells us where the contiguous complete run starts
echo "--- Contiguous complete run from tip ---"

# Get just the slot numbers and is_full in reverse order
REVERSED=$(echo "$OUTPUT" | paste - - | awk '{
    slot = $2;
    full = ($NF == "true") ? 1 : 0;
    print slot, full
}' | sort -rn)

CONTIGUOUS=0
FIRST_FULL=""
while IFS=' ' read -r slot full; do
    if [ "$full" -eq 1 ]; then
        CONTIGUOUS=$((CONTIGUOUS + 1))
        FIRST_FULL="$slot"
    else
        break
    fi
done <<< "$REVERSED"

if [ -n "$FIRST_FULL" ]; then
    echo "Contiguous complete slots from tip: $CONTIGUOUS"
    echo "Run starts at slot: $FIRST_FULL"
    echo "Run ends at slot: $HIGHEST"
    echo ""
    echo "A snapshot with slot >= $FIRST_FULL would replay from local blockstore."

    # Check against mainnet
    MAINNET_SLOT=$(curl -s -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"getSlot","params":[{"commitment":"finalized"}]}' \
        https://api.mainnet-beta.solana.com | grep -oP '"result":\K[0-9]+')

    GAP=$((MAINNET_SLOT - HIGHEST))
    echo "Mainnet tip: $MAINNET_SLOT (blockstore is $GAP slots behind tip)"

    if [ "$CONTIGUOUS" -gt 100 ]; then
        echo ""
        echo ">>> READY: $CONTIGUOUS contiguous complete slots. Safe to download a snapshot."
    else
        echo ""
        echo ">>> NOT READY: Only $CONTIGUOUS contiguous complete slots. Wait for more."
    fi
else
    echo "No contiguous complete run from tip found."
fi
