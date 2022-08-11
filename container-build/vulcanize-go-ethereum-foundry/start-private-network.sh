#!/bin/bash

set -ex

# clean up
trap 'killall geth' EXIT
trap "exit 1" SIGINT SIGTERM

ETHDIR="/root/ethereum"
mkdir -p $ETHDIR
/bin/bash deploy-local-network.sh --rpc-addr 0.0.0.0 --db-user $DB_USER --db-password $DB_PASSWORD --db-name $DB_NAME \
  --db-host $DB_HOST --db-port $DB_PORT --db-write $DB_WRITE --dir "$ETHDIR" --address $ADDRESS \
  --db-type $DB_TYPE --db-driver $DB_DRIVER --db-waitforsync $DB_WAIT_FOR_SYNC --chain-id $CHAIN_ID --extra-args "$EXTRA_START_ARGS" &

# give it a few secs to start up
COUNT=0
ATTEMPTS=15
until $(nc -v localhost 8545) || [[ $COUNT -eq $ATTEMPTS ]]; do echo -e "$(( COUNT++ ))... \c"; sleep 10; done
[[ $COUNT -eq $ATTEMPTS ]] && echo "Could not connect to localhost 8545" && (exit 1)

# Run tests
cd stateful
forge build
forge test --fork-url http://localhost:8545

# Deploy contracts

ETH_KEYSTORE_FILES=()
echo "ETH KEYSTORE: $ETHDIR/keystore"
for entry in `ls $ETHDIR/keystore`; do
    ETH_KEYSTORE_FILES+=("${ETHDIR}/keystore/${entry}")
done

echo "ETH_KEYSTORE_FILES: $ETH_KEYSTORE_FILES"
ETH_KEYSTORE_FILE=${ETH_KEYSTORE_FILES[0]}

mkdir -p ~/transaction_info
echo $ETH_KEYSTORE_FILE > ~/transaction_info/CURRENT_ETH_KEYSTORE_FILE
echo $ETHDIR > ~/transaction_info/ETHDIR

if [ "${#ETH_KEYSTORE_FILES[@]}" -eq 1 ]; then
    echo "Only one KEYSTORE"
else
    echo "WARNING: More than one file in keystore: ${ETH_KEYSTORE_FILES}"
fi

DEPLOYED_ADDRESS=$(forge create --keystore $(cat ~/transaction_info/CURRENT_ETH_KEYSTORE_FILE) --rpc-url http://127.0.0.1:8545 --constructor-args 1 --password $(cat ${ETHDIR}/config/password) --legacy /root/stateful/src/Stateful.sol:Stateful | grep "Deployed to:" | cut -d " " -f 3)
echo "Contract has been deployed to: $DEPLOYED_ADDRESS"

echo $DEPLOYED_ADDRESS > ~/transaction_info/STATEFUL_TEST_DEPLOYED_ADDRESS
# Call a transaction

#TX_OUT=$(cast send --keystore $ETH_KEYSTORE_FILE --rpc-url http://127.0.0.1:8545 --password "" --legacy $DEPLOYED_ADDRESS "off()")
TX_OUT=$(cast send --keystore $(cat ~/transaction_info/CURRENT_ETH_KEYSTORE_FILE) --rpc-url http://127.0.0.1:8545 --password $(cat $(cat ~/transaction_info/ETHDIR)/config/password) --legacy $(cat ~/transaction_info/STATEFUL_TEST_DEPLOYED_ADDRESS) "inc()")
echo 'cast send --keystore $(cat ~/transaction_info/CURRENT_ETH_KEYSTORE_FILE) --rpc-url http://127.0.0.1:8545 --password $(cat $(cat ~/transaction_info/ETHDIR)/config/password) --legacy $(cat ~/transaction_info/STATEFUL_TEST_DEPLOYED_ADDRESS) "inc()" ' > ~/transaction_info/NEW_TRANSACTION
# Simply run the command below whenever you want to call the smart contract and create a new block
chmod +x ~/transaction_info/NEW_TRANSACTION


echo "TX OUTPUT: $TX_OUT"


# Run forever
tail -f /dev/null
