#!/bin/bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_L1_CHAIN_ID="${CERC_L1_CHAIN_ID:-${DEFAULT_CERC_L1_CHAIN_ID}}"
CERC_L1_RPC="${CERC_L1_RPC:-${DEFAULT_CERC_L1_RPC}}"

CERC_L1_ACCOUNTS_CSV_URL="${CERC_L1_ACCOUNTS_CSV_URL:-${DEFAULT_CERC_L1_ACCOUNTS_CSV_URL}}"

export DEPLOYMENT_CONTEXT="$CERC_L1_CHAIN_ID"
# Optional create2 salt for deterministic deployment of contract implementations
export IMPL_SALT=$(openssl rand -hex 32)

echo "Using L1 RPC endpoint ${CERC_L1_RPC}"

# Exit if a deployment already exists (on restarts)
if [ -d "/l1-deployment/$DEPLOYMENT_CONTEXT" ]; then
  echo "Deployment directory /l1-deployment/$DEPLOYMENT_CONTEXT, checking OptimismPortal deployment"

  OPTIMISM_PORTAL_ADDRESS=$(cat /l1-deployment/$DEPLOYMENT_CONTEXT/OptimismPortal.json | jq -r .address)
  contract_code=$(cast code $OPTIMISM_PORTAL_ADDRESS --rpc-url $CERC_L1_RPC)

  if [ -z "${contract_code#0x}" ]; then
    echo "Error: A deployment directory was found in the volume, but no contract code was found on-chain at the associated address. Please clear L1 deployment volume before restarting."
    exit 1
  else
    echo "Deployment found, exiting (successfully)."
    exit 0
  fi
fi

wait_for_block() {
  local block="$1"  # Block to wait for
  local timeout="$2"  # Max time to wait in seconds

  echo "Waiting for block $block."
  i=0
  loops=$(($timeout/10))
  while [ -z "$block_result" ] && [[ "$i" -lt "$loops" ]]; do
    sleep 10
    echo "Checking..."
    block_result=$(cast block $block --rpc-url $CERC_L1_RPC | grep -E "(timestamp|hash|number)" || true)
    i=$(($i + 1))
  done
}

# We need four accounts and their private keys for the deployment: Admin, Proposer, Batcher, and Sequencer
# If $CERC_L1_ADDRESS and $CERC_L1_PRIV_KEY have been set, we'll assign it to Admin and generate/fund the remaining three accounts from it
# If not, we'll assume the L1 is the stack's own fixturenet-eth and use the pre-funded accounts/keys from $CERC_L1_ACCOUNTS_CSV_URL
if [ -n "$CERC_L1_ADDRESS" ] && [ -n "$CERC_L1_PRIV_KEY" ]; then
  wallet1=$(cast wallet new)
  wallet2=$(cast wallet new)
  wallet3=$(cast wallet new)
  # Admin
  ADMIN=$CERC_L1_ADDRESS
  ADMIN_KEY=$CERC_L1_PRIV_KEY
  # Proposer
  PROPOSER=$(echo "$wallet1" | awk '/Address:/{print $2}')
  PROPOSER_KEY=$(echo "$wallet1" | awk '/Private key:/{print $3}')
  # Batcher
  BATCHER=$(echo "$wallet2" | awk '/Address:/{print $2}')
  BATCHER_KEY=$(echo "$wallet2" | awk '/Private key:/{print $3}')
  # Sequencer
  SEQ=$(echo "$wallet3" | awk '/Address:/{print $2}')
  SEQ_KEY=$(echo "$wallet3" | awk '/Private key:/{print $3}')

  echo "Funding accounts."
  wait_for_block 1 300
  cast send --from $ADMIN --rpc-url $CERC_L1_RPC --value 5ether $PROPOSER --private-key $ADMIN_KEY
  cast send --from $ADMIN --rpc-url $CERC_L1_RPC --value 10ether $BATCHER --private-key $ADMIN_KEY
  cast send --from $ADMIN --rpc-url $CERC_L1_RPC --value 2ether $SEQ --private-key $ADMIN_KEY
else
  curl -o accounts.csv $CERC_L1_ACCOUNTS_CSV_URL
  # Admin
  ADMIN=$(awk -F ',' 'NR == 1 {print $2}' accounts.csv)
  ADMIN_KEY=$(awk -F ',' 'NR == 1 {print $3}' accounts.csv)
  # Proposer
  PROPOSER=$(awk -F ',' 'NR == 2 {print $2}' accounts.csv)
  PROPOSER_KEY=$(awk -F ',' 'NR == 2 {print $3}' accounts.csv)
  # Batcher
  BATCHER=$(awk -F ',' 'NR == 3 {print $2}' accounts.csv)
  BATCHER_KEY=$(awk -F ',' 'NR == 3 {print $3}' accounts.csv)
  # Sequencer
  SEQ=$(awk -F ',' 'NR == 4 {print $2}' accounts.csv)
  SEQ_KEY=$(awk -F ',' 'NR == 4 {print $3}' accounts.csv)
fi

echo "Using accounts:"
echo -e "Admin: $ADMIN\nProposer: $PROPOSER\nBatcher: $BATCHER\nSequencer: $SEQ"

# These accounts will be needed by other containers, so write them to a shared volume
echo "Writing accounts/private keys to volume l2_accounts."
accounts_json=$(jq -n \
  --arg Admin "$ADMIN" --arg AdminKey "$ADMIN_KEY" \
  --arg Proposer "$PROPOSER" --arg ProposerKey "$PROPOSER_KEY" \
  --arg Batcher "$BATCHER" --arg BatcherKey "$BATCHER_KEY" \
  --arg Seq "$SEQ" --arg SeqKey "$SEQ_KEY" \
  '{Admin: $Admin, AdminKey: $AdminKey, Proposer: $Proposer, ProposerKey: $ProposerKey, Batcher: $Batcher, BatcherKey: $BatcherKey, Seq: $Seq, SeqKey: $SeqKey}')
echo "$accounts_json" > "/l2-accounts/accounts.json"

# Get a finalized L1 block to set as the starting point for the L2 deployment
# If the chain is a freshly created fixturenet-eth, a finalized block won't be available for many minutes; rather than wait, we can use block 1
echo "Checking L1 for finalized block..."
finalized=$(cast block finalized --rpc-url $CERC_L1_RPC | grep -E "(timestamp|hash|number)" || true)

if [ -n "$finalized" ]; then
  # finalized block was found
  start_block=$finalized
else
  # assume fresh chain and use block 1 instead
  echo "No finalized block. Using block 1 instead."
  # wait for 20 or so blocks to be safe
  wait_for_block 24 300
  start_block=$(cast block 1 --rpc-url $CERC_L1_RPC | grep -E "(timestamp|hash|number)" || true)
fi

if [ -z "$start_block" ]; then
  echo "Unable to query chain for starting block. Exiting..."
  exit 1
fi

BLOCKHASH=$(echo $start_block | awk -F ' ' '{print $2}')
HEIGHT=$(echo $start_block | awk -F ' ' '{print $4}')
TIMESTAMP=$(echo $start_block | awk -F ' ' '{print $6}')

echo "Using block as deployment point:"
echo "Height: $HEIGHT"
echo "Hash: $BLOCKHASH"
echo "Timestamp: $TIMESTAMP"

# Fill out the deployment template (./deploy-config/getting-started.json) with our values:
echo "Writing deployment config."
deploy_config_file="deploy-config/$DEPLOYMENT_CONTEXT.json"
cp deploy-config/getting-started.json $deploy_config_file
sed -i "s/\"l1ChainID\": .*/\"l1ChainID\": $DEPLOYMENT_CONTEXT,/g" $deploy_config_file
sed -i "s/ADMIN/$ADMIN/g" $deploy_config_file
sed -i "s/PROPOSER/$PROPOSER/g" $deploy_config_file
sed -i "s/BATCHER/$BATCHER/g" $deploy_config_file
sed -i "s/SEQUENCER/$SEQ/g" $deploy_config_file
sed -i "s/BLOCKHASH/$BLOCKHASH/g" $deploy_config_file
sed -i "s/TIMESTAMP/$TIMESTAMP/g" $deploy_config_file

mkdir -p deployments/$DEPLOYMENT_CONTEXT

# Deployment requires the create2 deterministic proxy contract be published on L1 at address 0x4e59b44847b379578588920ca78fbf26c0b4956c
# See: https://github.com/Arachnid/deterministic-deployment-proxy
echo "Deploying create2 proxy contract..."
echo "Funding deployment signer address"
deployment_signer="0x3fab184622dc19b6109349b94811493bf2a45362"
cast send --from $ADMIN --rpc-url $CERC_L1_RPC --value 0.5ether $deployment_signer --private-key $ADMIN_KEY
echo "Deploying contract..."
raw_bytes="0xf8a58085174876e800830186a08080b853604580600e600039806000f350fe7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe03601600081602082378035828234f58015156039578182fd5b8082525050506014600cf31ba02222222222222222222222222222222222222222222222222222222222222222a02222222222222222222222222222222222222222222222222222222222222222"

cast publish --rpc-url $CERC_L1_RPC $raw_bytes

# Create the L2 deployment
echo "Deploying L1 Optimism contracts..."
forge script scripts/Deploy.s.sol:Deploy --private-key $ADMIN_KEY --broadcast --rpc-url $CERC_L1_RPC
forge script scripts/Deploy.s.sol:Deploy --sig 'sync()' --private-key $ADMIN_KEY --broadcast --rpc-url $CERC_L1_RPC

echo "*************************************"
echo "Done deploying contracts."

# Copy files needed by other containers to the appropriate shared volumes
echo "Copying deployment artifacts volume l1_deployment and deploy-config to volume l2_config"
cp -a /app/packages/contracts-bedrock/deployments/$DEPLOYMENT_CONTEXT /l1-deployment
cp /app/packages/contracts-bedrock/deploy-config/$DEPLOYMENT_CONTEXT.json /l2-config
openssl rand -hex 32 > /l2-config/l2-jwt.txt

echo "Deployment successful. Exiting."
