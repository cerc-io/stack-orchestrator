#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "Using L2 RPC endpoint ${L2_GETH_RPC}"

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
jq --arg rpcUrl "$L2_GETH_RPC" '.rpcUrl = $rpcUrl' secrets.json > secrets_updated.json && mv secrets_updated.json secrets.json

export RPC_URL="${L2_GETH_RPC}"

# Check if DEPLOYED_CONTRACT environment variable set to skip contract deployment
if [[ -n "$DEPLOYED_CONTRACT" ]]; then
  echo "DEPLOYED_CONTRACT is set to '$DEPLOYED_CONTRACT'"
  echo "Exiting without deploying contract"
  exit 0
fi

# Check and exit if a deployment already exists (on restarts)
if [ -f ./config.json ]; then
  echo "config.json already exists, checking the contract deployment"

  # Read JSON file
  DEPLOYMENT_DETAILS=$(cat config.json)
  CONTRACT_ADDRESS=$(echo "$DEPLOYMENT_DETAILS" | jq -r '.address')

  cd ../hardhat
  if yarn verifyDeployment --network optimism --contract "${CONTRACT_ADDRESS}"; then
    echo "Deployment verfication successful"
    cd ../server
  else
    echo "Deployment verfication failed, please clear MobyMask deployment volume before starting"
    exit 1
  fi
fi

# Wait until balance for deployer account is updated
cd ../hardhat
while true; do
  ACCOUNT_BALANCE=$(yarn balance --network optimism "$PRIVATE_KEY_DEPLOYER" | grep ETH)

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
