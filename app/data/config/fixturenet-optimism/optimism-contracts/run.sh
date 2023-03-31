#!/bin/bash
set -e

# TODO Support restarts; fixturenet-eth-geth currently starts fresh on a restart
# Exit if a deployment already exists (on restarts)
# if [ -d "deployments/getting-started" ]; then
#     echo "Deployment directory deployments/getting-started already exists, exiting"
#     exit 0
# fi

# Append tasks/index.ts file
echo "import './rekey-json'" >> tasks/index.ts
echo "import './send-balance'" >> tasks/index.ts

# Update the chainId in the hardhat config
sed -i "/getting-started/ {n; s/.*chainId.*/      chainId: $CHAIN_ID,/}" hardhat.config.ts

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

# Read the private key of a L1 account
# TODO: Take from env if /geth-accounts volume doesn't exist to allow using separately running L1
L1_ADDRESS=$(head -n 1 /geth-accounts/accounts.csv | cut -d ',' -f 2)
L1_PRIV_KEY=$(head -n 1 /geth-accounts/accounts.csv | cut -d ',' -f 3)

# Send balances to the above L2 addresses
yarn hardhat send-balance --to "${ADMIN_ADDRESS}" --amount 2 --private-key "${L1_PRIV_KEY}" --network getting-started
yarn hardhat send-balance --to "${PROPOSER_ADDRESS}" --amount 5 --private-key "${L1_PRIV_KEY}" --network getting-started
yarn hardhat send-balance --to "${BATCHER_ADDRESS}" --amount 1000 --private-key "${L1_PRIV_KEY}" --network getting-started

echo "Balances sent to L2 accounts"

# Select a finalized L1 block as the starting point for roll ups
# TODO Use web3.js to get the latest finalized block
until CAST_OUTPUT=$(cast block finalized --rpc-url "$L1_RPC"); do
    echo "Waiting for a finalized L1 block to exist, retrying after 10s"
    sleep 10
done

L1_BLOCKHASH=$(echo "$CAST_OUTPUT" | awk '/hash/{print $2}')
L1_BLOCKTIMESTAMP=$(echo "$CAST_OUTPUT" | awk '/timestamp/{print $2}')

# Update the deployment config
sed -i 's/"l2OutputOracleStartingTimestamp": TIMESTAMP/"l2OutputOracleStartingTimestamp": '"$L1_BLOCKTIMESTAMP"'/g' deploy-config/getting-started.json
jq --arg chainid "$CHAIN_ID" '.l1ChainID = ($chainid | tonumber)' deploy-config/getting-started.json > tmp.json && mv tmp.json deploy-config/getting-started.json

node update-config.js deploy-config/getting-started.json "$ADMIN_ADDRESS" "$PROPOSER_ADDRESS" "$BATCHER_ADDRESS" "$SEQUENCER_ADDRESS" "$L1_BLOCKHASH"

echo "Updated the deployment config"

# Create a .env file
echo "L1_RPC=$L1_RPC" > .env
echo "PRIVATE_KEY_DEPLOYER=$ADMIN_PRIV_KEY" >> .env

echo "Deploying the L1 smart contracts, this will take a while..."

# Deploy the L1 smart contracts
yarn hardhat deploy --network getting-started

echo "Deployed the L1 smart contracts"

# Read Proxy contarct's JSON and get the address
PROXY_JSON=$(cat deployments/getting-started/Proxy__OVM_L1StandardBridge.json)
PROXY_ADDRESS=$(echo "$PROXY_JSON" | jq -r '.address')

# Send balance to the above L2 address
# TODO: Send balance using second account to reflect in L2
yarn hardhat send-balance --to "${PROXY_ADDRESS}" --amount 1 --private-key "${L1_PRIV_KEY}" --network getting-started

echo "Balance sent to Proxy L2 contract"
echo "Use account ${L1_ADDRESS} to deploy contracts to L2"
echo "Done"
