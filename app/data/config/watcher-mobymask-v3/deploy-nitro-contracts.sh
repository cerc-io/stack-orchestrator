#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_NA_ADDRESS="${CERC_NA_ADDRESS:-${DEFAULT_CERC_NA_ADDRESS}}"
CERC_VPA_ADDRESS="${CERC_VPA_ADDRESS:-${DEFAULT_CERC_VPA_ADDRESS}}"
CERC_CA_ADDRESS="${CERC_CA_ADDRESS:-${DEFAULT_CERC_CA_ADDRESS}}"

NITRO_ADDRESSES_FILE_PATH="/nitro/nitro-addresses.json"

# Check if CERC_NITRO_CONTRACTS environment variable set to skip contract deployment
if [ -n "$CERC_NA_ADDRESS" ]; then
  echo "CERC_NA_ADDRESS is set to '$CERC_NA_ADDRESS'"
  echo "CERC_VPA_ADDRESS is set to '$CERC_VPA_ADDRESS'"
  echo "CERC_CA_ADDRESS is set to '$CERC_CA_ADDRESS'"
  echo "Using the above addresses and skipping Nitro contracts deployment"

  # Create the required JSON and write it to a file
  nitro_addresses_json=$(jq -n \
    --arg na "$CERC_NA_ADDRESS" \
    --arg vpa "$CERC_VPA_ADDRESS" \
    --arg ca "$CERC_CA_ADDRESS" \
    '.nitroAdjudicatorAddress = $na | .virtualPaymentAppAddress = $vpa | .consensusAppAddress = $ca')
  echo "$nitro_addresses_json" > "${NITRO_ADDRESSES_FILE_PATH}"

  exit
fi

# Check and exit if a deployment already exists (on restarts)
if [ -f ${NITRO_ADDRESSES_FILE_PATH} ]; then
  echo "${NITRO_ADDRESSES_FILE_PATH} already exists, skipping Nitro contracts deployment"
  exit
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

echo "RPC_URL=${CERC_L2_GETH_RPC}" > .env
echo "NITRO_ADDRESSES_FILE_PATH=${NITRO_ADDRESSES_FILE_PATH}" >> .env
echo "PRIVATE_KEY=${CERC_PRIVATE_KEY_DEPLOYER}" >> .env

yarn ts-node --esm deploy-nitro-contracts.ts
