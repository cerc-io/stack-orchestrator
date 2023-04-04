#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

# TODO: Add in container build or use other tool
echo "Installing jq"
apk update && apk add jq

# Initialize op-geth if datadir/geth not found
if [ -f /op-node/jwt.txt ] && [ -d datadir/geth ]; then
  echo "Found existing datadir, skipping initialization"
else
  echo "Initializing op-geth"

  mkdir datadir
  echo "pwd" > datadir/password

  # Get SEQUENCER KEY from keys.json
  SEQUENCER_KEY=$(jq -r '.Sequencer.privateKey' /l2-accounts/keys.json | tr -d '"')
  echo $SEQUENCER_KEY > datadir/block-signer-key

  geth account import --datadir=datadir --password=datadir/password datadir/block-signer-key

  while [ ! -f "/op-node/jwt.txt" ]
  do
    echo "Config files not created. Checking after 5 seconds."
    sleep 5
  done

  echo "Config files created by op-node, proceeding with the initialization..."

  geth init --datadir=datadir /op-node/genesis.json
  echo "Node Initialized"
fi

SEQUENCER_ADDRESS=$(jq -r '.Sequencer.address' /l2-accounts/keys.json | tr -d '"')
echo "SEQUENCER_ADDRESS: ${SEQUENCER_ADDRESS}"

# Run op-geth
geth \
  --datadir ./datadir \
  --http \
  --http.corsdomain="*" \
  --http.vhosts="*" \
  --http.addr=0.0.0.0 \
  --http.api=web3,debug,eth,txpool,net,engine \
  --ws \
  --ws.addr=0.0.0.0 \
  --ws.port=8546 \
  --ws.origins="*" \
  --ws.api=debug,eth,txpool,net,engine \
  --syncmode=full \
  --gcmode=full \
  --nodiscover \
  --maxpeers=0 \
  --networkid=42069 \
  --authrpc.vhosts="*" \
  --authrpc.addr=0.0.0.0 \
  --authrpc.port=8551 \
  --authrpc.jwtsecret=/op-node/jwt.txt \
  --rollup.disabletxpoolgossip=true \
  --password=./datadir/password \
  --allow-insecure-unlock \
  --mine \
  --miner.etherbase=$SEQUENCER_ADDRESS \
  --unlock=$SEQUENCER_ADDRESS
