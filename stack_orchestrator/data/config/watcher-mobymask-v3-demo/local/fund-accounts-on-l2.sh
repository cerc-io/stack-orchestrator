#!/bin/bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "*************************************"

CERC_L1_RPC="${CERC_L1_RPC:-${DEFAULT_CERC_L1_RPC}}"
CERC_L1_CHAIN_ID="${CERC_L1_CHAIN_ID:-${DEFAULT_CERC_L1_CHAIN_ID}}"
CERC_L1_ACCOUNTS_CSV_URL="${CERC_L1_ACCOUNTS_CSV_URL:-${DEFAULT_CERC_L1_ACCOUNTS_CSV_URL}}"

# Fixture accounts
WATCHER_1_ACCOUNT=0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
WATCHER_2_ACCOUNT=0x70997970C51812dc3A010C7d01b50e0d17dc79C8
WATCHER_3_ACCOUNT=0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65
NITRO_APP_ACCOUNT=0xbDA5747bFD65F08deb54cb465eB87D40e51B197E

WATCHER_1_ACCOUNT_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
WATCHER_2_ACCOUNT_KEY=0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d
WATCHER_3_ACCOUNT_KEY=0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a
NITRO_APP_ACCOUNT_KEY=0x689af8efa8c651a91ad287602527f3af2fe9f6501a7ac4b061667b5a93e037fd

# Check if watcher 1 account already funded
WATCHER_1_ACCOUNT_BALANCE=$(cast balance ${WATCHER_1_ACCOUNT} --rpc-url $CERC_L1_RPC)
echo "WATCHER_1_ACCOUNT_BALANCE ${WATCHER_1_ACCOUNT_BALANCE}"
if [ "$WATCHER_1_ACCOUNT_BALANCE" != "0" ]; then
  echo "Watcher account already funded, exiting."
  exit 0
fi

echo "Funding accounts on L2"

# Fetch the L1 funded accounts
curl -o accounts.csv $CERC_L1_ACCOUNTS_CSV_URL

# Use the accounts other than the ones used for Optimism deployment
ACCOUNT_1=$(awk -F ',' 'NR == 5 {print $2}' accounts.csv)
ACCOUNT_1_KEY=$(awk -F ',' 'NR == 5 {print $3}' accounts.csv)

ACCOUNT_2=$(awk -F ',' 'NR == 6 {print $2}' accounts.csv)
ACCOUNT_2_KEY=$(awk -F ',' 'NR == 6 {print $3}' accounts.csv)

# Get the bridge contract address
DEPLOYMENT_CONTEXT="$CERC_L1_CHAIN_ID"
BRIDGE=$(cat /l1-deployment/$DEPLOYMENT_CONTEXT/L1StandardBridgeProxy.json | jq -r .address)

# Send balance to bridge contract on L1
cast send --rpc-url $CERC_L1_RPC --from $ACCOUNT_1 --value 10000ether $BRIDGE --private-key $ACCOUNT_1_KEY
cast send --rpc-url $CERC_L1_RPC --from $ACCOUNT_2 --value 10000ether $BRIDGE --private-key $ACCOUNT_2_KEY

echo "Following accounts have been funded; use them for transactions on L2:"
echo "${ACCOUNT_1}"
echo "${ACCOUNT_2}"

echo "*************************************"
echo "Funding the watcher and app Nitro accounts on L2"

cast send --rpc-url $CERC_L1_RPC --from $ACCOUNT_1 --value 200ether $WATCHER_1_ACCOUNT --private-key $ACCOUNT_1_KEY
cast send --rpc-url $CERC_L1_RPC --from $ACCOUNT_1 --value 200ether $WATCHER_2_ACCOUNT --private-key $ACCOUNT_1_KEY
cast send --rpc-url $CERC_L1_RPC --from $ACCOUNT_1 --value 200ether $WATCHER_3_ACCOUNT --private-key $ACCOUNT_1_KEY
cast send --rpc-url $CERC_L1_RPC --from $ACCOUNT_1 --value 200ether $NITRO_APP_ACCOUNT --private-key $ACCOUNT_1_KEY

cast send --rpc-url $CERC_L1_RPC --from $WATCHER_1_ACCOUNT --value 100ether $BRIDGE --private-key $WATCHER_1_ACCOUNT_KEY
sleep 5
cast send --rpc-url $CERC_L1_RPC --from $WATCHER_2_ACCOUNT --value 100ether $BRIDGE --private-key $WATCHER_2_ACCOUNT_KEY
sleep 5
cast send --rpc-url $CERC_L1_RPC --from $WATCHER_3_ACCOUNT --value 100ether $BRIDGE --private-key $WATCHER_3_ACCOUNT_KEY
sleep 5
cast send --rpc-url $CERC_L1_RPC --from $NITRO_APP_ACCOUNT --value 100ether $BRIDGE --private-key $NITRO_APP_ACCOUNT_KEY

echo "Done, exiting."
