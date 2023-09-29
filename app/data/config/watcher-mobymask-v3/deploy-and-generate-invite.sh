#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

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
