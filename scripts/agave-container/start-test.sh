#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------
# Start solana-test-validator with optional SPL token setup
#
# Environment variables:
#   FACILITATOR_PUBKEY  - facilitator fee-payer public key (base58)
#   SERVER_PUBKEY       - server/payee wallet public key (base58)
#   CLIENT_PUBKEY       - client/payer wallet public key (base58)
#   MINT_DECIMALS       - token decimals (default: 6, matching USDC)
#   MINT_AMOUNT         - amount to mint to client (default: 1000000000)
#   LEDGER_DIR          - ledger directory (default: /data/ledger)
# -----------------------------------------------------------------------

LEDGER_DIR="${LEDGER_DIR:-/data/ledger}"
MINT_DECIMALS="${MINT_DECIMALS:-6}"
MINT_AMOUNT="${MINT_AMOUNT:-1000000000}"
SETUP_MARKER="${LEDGER_DIR}/.setup-done"

sudo chown -R "$(id -u):$(id -g)" "$LEDGER_DIR" 2>/dev/null || true

# Start test-validator in the background
solana-test-validator \
  --ledger "${LEDGER_DIR}" \
  --rpc-port 8899 \
  --bind-address 0.0.0.0 \
  --quiet &

VALIDATOR_PID=$!

# Wait for RPC to become available
echo "Waiting for test-validator RPC..."
for i in $(seq 1 60); do
  if solana cluster-version --url http://127.0.0.1:8899 >/dev/null 2>&1; then
    echo "Test-validator is ready (attempt ${i})"
    break
  fi
  sleep 1
done

solana config set --url http://127.0.0.1:8899

# Only run setup once (idempotent via marker file)
if [ ! -f "${SETUP_MARKER}" ]; then
  echo "Running first-time setup..."

  # Airdrop SOL to all wallets for gas
  for PUBKEY in "${FACILITATOR_PUBKEY:-}" "${SERVER_PUBKEY:-}" "${CLIENT_PUBKEY:-}"; do
    if [ -n "${PUBKEY}" ]; then
      echo "Airdropping 100 SOL to ${PUBKEY}..."
      solana airdrop 100 "${PUBKEY}" --url http://127.0.0.1:8899 || true
    fi
  done

  # Create a USDC-equivalent SPL token mint if any pubkeys are set
  if [ -n "${CLIENT_PUBKEY:-}" ] || [ -n "${FACILITATOR_PUBKEY:-}" ] || [ -n "${SERVER_PUBKEY:-}" ]; then
    MINT_AUTHORITY_FILE="${LEDGER_DIR}/mint-authority.json"
    if [ ! -f "${MINT_AUTHORITY_FILE}" ]; then
      solana-keygen new --no-bip39-passphrase --outfile "${MINT_AUTHORITY_FILE}" --force
      MINT_AUTH_PUBKEY=$(solana-keygen pubkey "${MINT_AUTHORITY_FILE}")
      solana airdrop 10 "${MINT_AUTH_PUBKEY}" --url http://127.0.0.1:8899
    fi

    MINT_ADDRESS_FILE="${LEDGER_DIR}/usdc-mint-address.txt"
    if [ ! -f "${MINT_ADDRESS_FILE}" ]; then
      spl-token create-token \
        --decimals "${MINT_DECIMALS}" \
        --mint-authority "${MINT_AUTHORITY_FILE}" \
        --url http://127.0.0.1:8899 \
        2>&1 | grep "Creating token" | awk '{print $3}' > "${MINT_ADDRESS_FILE}"
      echo "Created USDC mint: $(cat "${MINT_ADDRESS_FILE}")"
    fi

    USDC_MINT=$(cat "${MINT_ADDRESS_FILE}")

    # Create ATAs and mint tokens for the client
    if [ -n "${CLIENT_PUBKEY:-}" ]; then
      echo "Creating ATA for client ${CLIENT_PUBKEY}..."
      spl-token create-account "${USDC_MINT}" \
        --owner "${CLIENT_PUBKEY}" \
        --fee-payer "${MINT_AUTHORITY_FILE}" \
        --url http://127.0.0.1:8899 || true

      echo "Minting ${MINT_AMOUNT} tokens to client..."
      spl-token mint "${USDC_MINT}" "${MINT_AMOUNT}" \
        --recipient-owner "${CLIENT_PUBKEY}" \
        --mint-authority "${MINT_AUTHORITY_FILE}" \
        --url http://127.0.0.1:8899 || true
    fi

    # Create ATAs for server and facilitator
    for PUBKEY in "${SERVER_PUBKEY:-}" "${FACILITATOR_PUBKEY:-}"; do
      if [ -n "${PUBKEY}" ]; then
        echo "Creating ATA for ${PUBKEY}..."
        spl-token create-account "${USDC_MINT}" \
          --owner "${PUBKEY}" \
          --fee-payer "${MINT_AUTHORITY_FILE}" \
          --url http://127.0.0.1:8899 || true
      fi
    done

    # Expose mint address for other containers
    cp "${MINT_ADDRESS_FILE}" /tmp/usdc-mint-address.txt 2>/dev/null || true
  fi

  touch "${SETUP_MARKER}"
  echo "Setup complete."
fi

echo "solana-test-validator running (PID ${VALIDATOR_PID})"
wait ${VALIDATOR_PID}
