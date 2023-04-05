#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

if [ -f /geth-accounts/accounts.csv ]; then
  echo "Using L1 private key from the mounted volume"
  # Read the private key of L1 account to deploy contract
  PRIVATE_KEY_DEPLOYER=$(head -n 1 /geth-accounts/accounts.csv | cut -d ',' -f 3)
else
  echo "Using PRIVATE_KEY_DEPLOYER from env"
fi

# Set the private key
jq --arg privateKey "$PRIVATE_KEY_DEPLOYER" '.privateKey = $privateKey' secrets-template.json > secrets.json

# Set the RPC URL
export L2_GETH_URL="http://${L2_GETH_HOST}:${L2_GETH_PORT}"
jq --arg rpcUrl "$L2_GETH_URL" '.rpcUrl = $rpcUrl' secrets.json > secrets_updated.json && mv secrets_updated.json secrets.json

export RPC_URL="${L2_GETH_URL}"

# Check and exit if a deployment already exists (on restarts)
if [ -f ./config.json ]; then
  echo "config.json already exists, checking the contract deployment"

  # Read JSON file
  DEPLOYMENT_DETAILS=$(cat config.json)
  CONTRACT_ADDRESS=$(echo "$DEPLOYMENT_DETAILS" | jq -r '.address')

  cd ../hardhat
  if yarn hardhat verify-deployment --network deployment --contract "${CONTRACT_ADDRESS}"; then
    echo "Deployment verfication successful"
    cd ../server
  else
    echo "Deployment verfication failed, please clear MobyMask deployment volume before starting"
    exit 1
  fi
fi

# Wait until balance for deployer account is reflected
cd ../hardhat
while true; do
  ACCOUNT_BALANCE=$(yarn hardhat --network optimism balance $PRIVATE_KEY_DEPLOYER | grep ETH)

  if [ "$ACCOUNT_BALANCE" != "0.0 ETH" ]; then
    echo "Account balance updated: $ACCOUNT_BALANCE"
    break # exit the loop
  fi

  echo "Account balance not updated: $ACCOUNT_BALANCE"
  echo "Checking after 2 seconds"
  sleep 2
done

cd ../server
npm run deployAndGenerateInvite
