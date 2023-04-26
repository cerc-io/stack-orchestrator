#!/bin/bash

MY_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

GETH_EXPORT_MIN_BLOCK=${1:-${GETH_EXPORT_MIN_BLOCK:-1000}}

# Wait for block.
${MY_DIR}/status.sh $GETH_EXPORT_MIN_BLOCK
if [ $? -ne 0 ]; then
  echo "Unable to export ethdb." 1>&2
  exit 1
fi

# Stop geth.
echo -n "Exporting ethdb.... "
GETH_CONTAINER=`docker ps -q -f "name=${CERC_SO_COMPOSE_PROJECT}-fixturenet-eth-geth-2-1"`
if [ -z "$GETH_CONTAINER" ]; then 
  echo "not found"
  exit 1
fi

docker exec $GETH_CONTAINER sh -c 'rm -rf /root/tmp && mkdir -p /root/tmp/export'
docker exec $GETH_CONTAINER sh -c 'ln -s /opt/testnet/build/el/geth.json /root/tmp/export/genesis.json && ln -s /root/ethdata /root/tmp/export/'
docker exec $GETH_CONTAINER sh -c 'cat /root/tmp/export/genesis.json | jq ".config" > /root/tmp/export/genesis.config.json'

# Stop geth and zip up ethdb.
docker exec $GETH_CONTAINER sh -c 'curl -s --location "localhost:8545" --header "Content-Type: application/json" --data "{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"eth_getBlockByNumber\", \"params\": [\"0x0\", false]}" > /root/tmp/export/eth_getBlockByNumber_0x0.json'
docker exec $GETH_CONTAINER sh -c 'curl -s --location "localhost:8545" --header "Content-Type: application/json" --data "{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"eth_blockNumber\", \"params\": []}" > /root/tmp/export/eth_blockNumber.json'
docker exec $GETH_CONTAINER sh -c "killall geth && sleep 2 && tar chzf /root/tmp/ethdb.tgz -C /root/tmp/export ."

# Copy ethdb to host.
GETH_EXPORT_FILE=${2:-${GETH_EXPORT_FILE:-./ethdb.tgz}}
docker cp $GETH_CONTAINER:/root/tmp/ethdb.tgz $GETH_EXPORT_FILE
echo "$GETH_EXPORT_FILE"
docker exec $GETH_CONTAINER sh -c "rm -rf /root/tmp"

# Restart the container to get geth back up and running.
docker restart $GETH_CONTAINER >/dev/null
