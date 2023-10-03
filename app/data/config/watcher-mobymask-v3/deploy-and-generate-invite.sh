#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_ETH_RPC_ENDPOINT="${CERC_ETH_RPC_ENDPOINT:-${DEFAULT_CERC_ETH_RPC_ENDPOINT}}"
CERC_MOBYMASK_APP_BASE_URI="${CERC_MOBYMASK_APP_BASE_URI:-${DEFAULT_CERC_MOBYMASK_APP_BASE_URI}}"
CERC_DEPLOYED_CONTRACT="${CERC_DEPLOYED_CONTRACT:-${DEFAULT_CERC_DEPLOYED_CONTRACT}}"

# Check if CERC_DEPLOYED_CONTRACT environment variable set to skip contract deployment
if [ -n "$CERC_DEPLOYED_CONTRACT" ]; then
  echo "CERC_DEPLOYED_CONTRACT is set to '$CERC_DEPLOYED_CONTRACT'"
  echo "Skipping contract deployment"
  exit 0
fi

echo "Using ETH RPC endpoint ${CERC_ETH_RPC_ENDPOINT}"

# Wait till ETH RPC endpoint is available with block number > 1
retry_interval=5
while true; do
  block_number_hex=$(curl -s -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' ${CERC_ETH_RPC_ENDPOINT} | jq -r '.result')

  # Check if the request call was successful
  if [ $? -ne 0 ]; then
    echo "RPC endpoint not yet available, retrying in $retry_interval seconds..."
    sleep $retry_interval
    continue
  fi

  # Convert hex to decimal
  block_number_dec=$(printf %u ${block_number_hex})

  # Check if block number is > 1 to avoid failures in the deployment
  if [ "$block_number_dec" -ge 1 ]; then
    echo "RPC endpoint is up"
    break
  else
    echo "RPC endpoint not yet available, retrying in $retry_interval seconds..."
    sleep $retry_interval
    continue
  fi
done

echo "Using CERC_PRIVATE_KEY_DEPLOYER from env"

# Create the required JSON and write it to a file
secrets_file="secrets.json"
secrets_json=$(jq -n \
  --arg privateKey "$CERC_PRIVATE_KEY_DEPLOYER" \
  --arg rpcUrl "$CERC_ETH_RPC_ENDPOINT" \
  --arg baseURI "$CERC_MOBYMASK_APP_BASE_URI" \
  '.privateKey = $privateKey | .rpcUrl = $rpcUrl | .baseURI = $baseURI')
echo "$secrets_json" > "${secrets_file}"

export RPC_URL="${CERC_ETH_RPC_ENDPOINT}"

# Check and exit if a deployment already exists (on restarts)
if [ -f ./config.json ]; then
  echo "config.json already exists, checking the contract deployment"

  # Read JSON file
  deployment_details=$(cat config.json)
  deployed_contract=$(echo "$deployment_details" | jq -r '.address')

  cd ../hardhat
  if yarn verifyDeployment --network optimism --contract "${deployed_contract}"; then
    echo "Deployment verfication successful"
    cd ../server
  else
    echo "Deployment verfication failed, please clear MobyMask deployment volume before starting"
    exit 1
  fi
fi

npm run deployAndGenerateInvite
