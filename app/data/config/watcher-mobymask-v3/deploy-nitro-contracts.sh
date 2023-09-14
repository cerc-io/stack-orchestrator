#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_L2_GETH_RPC="${CERC_L2_GETH_RPC:-${DEFAULT_CERC_L2_GETH_RPC}}"
CERC_L1_ACCOUNTS_CSV_URL="${CERC_L1_ACCOUNTS_CSV_URL:-${DEFAULT_CERC_L1_ACCOUNTS_CSV_URL}}"
CERC_NITRO_CONTRACTS="${CERC_DEPLOYED_CONTRACT:-${DEFAULT_CERC_NITRO_CONTRACTS}}"

NITRO_ADDRESSES_FILE_PATH="/nitro/nitro-addresses.json"

# Check if CERC_NITRO_CONTRACTS environment variable set to skip contract deployment
if [ -n "$CERC_NITRO_CONTRACTS" ]; then
  echo "CERC_NITRO_CONTRACTS is set to '$CERC_NITRO_CONTRACTS'"
  echo "Skipping Nitro contracts deployment"
  exit 0
fi

echo "Using L2 RPC endpoint ${CERC_L2_GETH_RPC}"

if [ -n "$CERC_L1_ACCOUNTS_CSV_URL" ] && \
  l1_accounts_response=$(curl -L --write-out '%{http_code}' --silent --output /dev/null "$CERC_L1_ACCOUNTS_CSV_URL") && \
  [ "$l1_accounts_response" -eq 200 ];
then
  echo "Fetching L1 account credentials using provided URL"
  mkdir -p /geth-accounts
  wget -O /geth-accounts/accounts.csv "$CERC_L1_ACCOUNTS_CSV_URL"

  # Read the private key of an L1 account to deploy contract
  CERC_PRIVATE_KEY_DEPLOYER=$(head -n 1 /geth-accounts/accounts.csv | cut -d ',' -f 3)
else
  echo "Couldn't fetch L1 account credentials, using CERC_PRIVATE_KEY_DEPLOYER from env"
fi

# Check and exit if a deployment already exists (on restarts)
if [ -f ${NITRO_ADDRESSES_FILE_PATH} ]; then
  echo "${NITRO_ADDRESSES_FILE_PATH} already exists, skipping Nitro contracts deployment"
  exit
fi

export RPC_URL="${CERC_L2_GETH_RPC}"
export NITRO_ADDRESSES_FILE_PATH="${NITRO_ADDRESSES_FILE_PATH}"
export PRIVATE_KEY="${CERC_PRIVATE_KEY_DEPLOYER}"

yarn ts-node --esm ./src/deploy-nitro-contracts.ts
