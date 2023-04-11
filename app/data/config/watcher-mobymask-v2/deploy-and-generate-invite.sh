#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_L2_GETH_RPC="${CERC_L2_GETH_RPC:-${DEFAULT_CERC_L2_GETH_RPC}}"
CERC_PRIVATE_KEY_DEPLOYER="${CERC_PRIVATE_KEY_DEPLOYER:-${DEFAULT_CERC_PRIVATE_KEY_DEPLOYER}}"

CERC_MOBYMASK_APP_BASE_URI="${CERC_MOBYMASK_APP_BASE_URI:-${DEFAULT_CERC_MOBYMASK_APP_BASE_URI}}"
CERC_DEPLOYED_CONTRACT="${CERC_DEPLOYED_CONTRACT:-${DEFAULT_CERC_DEPLOYED_CONTRACT}}"

echo "Using L2 RPC endpoint ${CERC_L2_GETH_RPC}"

if [ -f /geth-accounts/accounts.csv ]; then
  echo "Using L1 private key from the mounted volume"
  # Read the private key of L1 account to deploy contract
  CERC_PRIVATE_KEY_DEPLOYER=$(head -n 1 /geth-accounts/accounts.csv | cut -d ',' -f 3)
else
  echo "Using CERC_PRIVATE_KEY_DEPLOYER from env"
fi

# Set the private key
jq --arg privateKey "$CERC_PRIVATE_KEY_DEPLOYER" '.privateKey = $privateKey' secrets-template.json > secrets.json

# Set the RPC URL
jq --arg rpcUrl "$CERC_L2_GETH_RPC" '.rpcUrl = $rpcUrl' secrets.json > secrets_updated.json && mv secrets_updated.json secrets.json

# Set the MobyMask app base URI
jq --arg baseURI "$CERC_MOBYMASK_APP_BASE_URI" '.baseURI = $baseURI' secrets.json > secrets_updated.json && mv secrets_updated.json secrets.json

export RPC_URL="${CERC_L2_GETH_RPC}"

# Check if CERC_DEPLOYED_CONTRACT environment variable set to skip contract deployment
if [ -n "$CERC_DEPLOYED_CONTRACT" ]; then
  echo "CERC_DEPLOYED_CONTRACT is set to '$CERC_DEPLOYED_CONTRACT'"
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
  ACCOUNT_BALANCE=$(yarn balance --network optimism "$CERC_PRIVATE_KEY_DEPLOYER" | grep ETH)

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
