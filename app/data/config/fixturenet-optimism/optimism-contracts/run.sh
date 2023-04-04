#!/bin/bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "Using L1 RPC endpoint ${L1_RPC}"

IMPORT_1="import './verify-contract-deployment'"
IMPORT_2="import './rekey-json'"
IMPORT_3="import './send-balance'"

# Append mounted tasks to tasks/index.ts file if not present
if ! grep -Fxq "$IMPORT_1" tasks/index.ts; then
  echo "$IMPORT_1" >> tasks/index.ts
  echo "$IMPORT_2" >> tasks/index.ts
  echo "$IMPORT_3" >> tasks/index.ts
fi

# Update the chainId in the hardhat config
sed -i "/getting-started/ {n; s/.*chainId.*/      chainId: $L1_CHAIN_ID,/}" hardhat.config.ts

# Exit if a deployment already exists (on restarts)
# Note: fixturenet-eth-geth currently starts fresh on a restart
if [ -d "deployments/getting-started" ]; then
  echo "Deployment directory deployments/getting-started found, checking SystemDictator deployment"

  # Read JSON file into variable
  SYSTEM_DICTATOR_DETAILS=$(cat deployments/getting-started/SystemDictator.json)

  # Parse JSON into variables
  SYSTEM_DICTATOR_ADDRESS=$(echo "$SYSTEM_DICTATOR_DETAILS" | jq -r '.address')
  SYSTEM_DICTATOR_TXHASH=$(echo "$SYSTEM_DICTATOR_DETAILS" | jq -r '.transactionHash')

  if yarn hardhat verify-contract-deployment --contract "${SYSTEM_DICTATOR_ADDRESS}" --transaction-hash "${SYSTEM_DICTATOR_TXHASH}"; then
    echo "Deployment verfication successful, exiting"
    exit 0
  else
    echo "Deployment verfication failed"
  fi
fi

# Generate the L2 account addresses
yarn hardhat rekey-json --output /l2-accounts/keys.json

# Read JSON file into variable
KEYS_JSON=$(cat /l2-accounts/keys.json)

# Parse JSON into variables
ADMIN_ADDRESS=$(echo "$KEYS_JSON" | jq -r '.Admin.address')
ADMIN_PRIV_KEY=$(echo "$KEYS_JSON" | jq -r '.Admin.privateKey')
PROPOSER_ADDRESS=$(echo "$KEYS_JSON" | jq -r '.Proposer.address')
BATCHER_ADDRESS=$(echo "$KEYS_JSON" | jq -r '.Batcher.address')
SEQUENCER_ADDRESS=$(echo "$KEYS_JSON" | jq -r '.Sequencer.address')

# Read the private key of L1 accounts
if [ -f /geth-accounts/accounts.csv ]; then
  echo "Using L1 account credentials from the mounted volume"
  L1_ADDRESS=$(head -n 1 /geth-accounts/accounts.csv | cut -d ',' -f 2)
  L1_PRIV_KEY=$(head -n 1 /geth-accounts/accounts.csv | cut -d ',' -f 3)
  L1_ADDRESS_2=$(awk -F, 'NR==2{print $(NF-1)}' /geth-accounts/accounts.csv)
  L1_PRIV_KEY_2=$(awk -F, 'NR==2{print $NF}' /geth-accounts/accounts.csv)
else
  echo "Using L1 account credentials from env"
fi

# Select a finalized L1 block as the starting point for roll ups
until FINALIZED_BLOCK=$(cast block finalized --rpc-url "$L1_RPC"); do
    echo "Waiting for a finalized L1 block to exist, retrying after 10s"
    sleep 10
done

L1_BLOCKNUMBER=$(echo "$FINALIZED_BLOCK" | awk '/number/{print $2}')
L1_BLOCKHASH=$(echo "$FINALIZED_BLOCK" | awk '/hash/{print $2}')
L1_BLOCKTIMESTAMP=$(echo "$FINALIZED_BLOCK" | awk '/timestamp/{print $2}')

echo "Selected L1 block ${L1_BLOCKNUMBER} as the starting block for roll ups"

# Send balances to the above L2 addresses
yarn hardhat send-balance --to "${ADMIN_ADDRESS}" --amount 2 --private-key "${L1_PRIV_KEY}" --network getting-started
yarn hardhat send-balance --to "${PROPOSER_ADDRESS}" --amount 5 --private-key "${L1_PRIV_KEY}" --network getting-started
yarn hardhat send-balance --to "${BATCHER_ADDRESS}" --amount 1000 --private-key "${L1_PRIV_KEY}" --network getting-started

echo "Balances sent to L2 accounts"

# Update the deployment config
sed -i 's/"l2OutputOracleStartingTimestamp": TIMESTAMP/"l2OutputOracleStartingTimestamp": '"$L1_BLOCKTIMESTAMP"'/g' deploy-config/getting-started.json
jq --arg chainid "$L1_CHAIN_ID" '.l1ChainID = ($chainid | tonumber)' deploy-config/getting-started.json > tmp.json && mv tmp.json deploy-config/getting-started.json

node update-config.js deploy-config/getting-started.json "$ADMIN_ADDRESS" "$PROPOSER_ADDRESS" "$BATCHER_ADDRESS" "$SEQUENCER_ADDRESS" "$L1_BLOCKHASH"

echo "Updated the deployment config"

# Create a .env file
echo "L1_RPC=$L1_RPC" > .env
echo "PRIVATE_KEY_DEPLOYER=$ADMIN_PRIV_KEY" >> .env

echo "Deploying the L1 smart contracts, this will take a while..."

# Deploy the L1 smart contracts
yarn hardhat deploy --network getting-started

echo "Deployed the L1 smart contracts"

# Read Proxy contract's JSON and get the address
PROXY_JSON=$(cat deployments/getting-started/Proxy__OVM_L1StandardBridge.json)
PROXY_ADDRESS=$(echo "$PROXY_JSON" | jq -r '.address')

# Send balance to the above Proxy contract in L1 for reflecting balance in L2
# First account
yarn hardhat send-balance --to "${PROXY_ADDRESS}" --amount 1 --private-key "${L1_PRIV_KEY}" --network getting-started
# Second account
yarn hardhat send-balance --to "${PROXY_ADDRESS}" --amount 1 --private-key "${L1_PRIV_KEY_2}" --network getting-started

echo "Balance sent to Proxy L2 contract"
echo "Use following accounts for transactions in L2:"
echo "${L1_ADDRESS}"
echo "${L1_ADDRESS_2}"
echo "Done"
