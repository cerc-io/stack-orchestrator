#!/bin/sh
set -e

mkdir datadir

echo "pwd" > datadir/password

# TODO: Add in container build or use other tool
echo "installing jq"
apk update && apk add jq

# Get SEQUENCER KEY from keys.json
SEQUENCER_KEY=$(jq -r '.Sequencer.privateKey' /l2-accounts/keys.json | tr -d '"')
echo $SEQUENCER_KEY > datadir/block-signer-key

geth account import --datadir=datadir --password=datadir/password datadir/block-signer-key

while [ ! -f "/op-node/jwt.txt" ]
do
  echo "Config files not created. Checking after 5 seconds."
  sleep 5
done

echo "Config files created by op-node, proceeding with script..."

cp /op-node/genesis.json ./
geth init --datadir=datadir genesis.json

SEQUENCER_ADDRESS=$(jq -r '.Sequencer.address' /l2-accounts/keys.json | tr -d '"')
echo "SEQUENCER_ADDRESS: ${SEQUENCER_ADDRESS}"
cp /op-node/jwt.txt ./
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
	--authrpc.jwtsecret=./jwt.txt \
	--rollup.disabletxpoolgossip=true \
	--password=./datadir/password \
	--allow-insecure-unlock \
	--mine \
	--miner.etherbase=$SEQUENCER_ADDRESS \
	--unlock=$SEQUENCER_ADDRESS
