#!/bin/bash

STATUSES=("geth to generate DAG" "beacon phase0" "beacon altair" "beacon bellatrix pre-merge" "beacon bellatrix merge")
STATUS=0


LIGHTHOUSE_BASE_URL=${LIGHTHOUSE_BASE_URL}
GETH_BASE_URL=${GETH_BASE_URL}

if [ -z "$LIGHTHOUSE_BASE_URL" ]; then
  LIGHTHOUSE_CONTAINER=`docker ps -q -f "name=fixturenet-eth-lighthouse-1-1"`
  LIGHTHOUSE_PORT=`docker port $LIGHTHOUSE_CONTAINER 8001 | cut -d':' -f2`
  LIGHTHOUSE_BASE_URL="http://localhost:${LIGHTHOUSE_PORT}"
fi

if [ -z "$GETH_BASE_URL" ]; then
  GETH_CONTAINER=`docker ps -q -f "name=fixturenet-eth-geth-1-1"`
  GETH_PORT=`docker port $GETH_CONTAINER 8545 | cut -d':' -f2`
  GETH_BASE_URL="http://localhost:${GETH_PORT}"
fi

function inc_status() {
  echo " DONE!"
  STATUS=$((STATUS + 1))
  if [ $STATUS -lt ${#STATUSES[@]} ]; then
    echo -n "Waiting for ${STATUSES[$STATUS]}..."
  fi
}

echo -n "Waiting for ${STATUSES[$STATUS]}..."
while [ $STATUS -lt ${#STATUSES[@]} ]; do
  sleep 1
  echo -n "."
  case $STATUS in
    0)
      result=`wget --no-check-certificate --quiet -O - --method POST --header 'Content-Type: application/json' \
        --body-data '{ "jsonrpc": "2.0", "id": 1, "method": "eth_getBlockByNumber", "params": ["0x3", false] }' $GETH_BASE_URL | jq -r '.result'`
      if [ ! -z "$result" ] && [ "null" != "$result" ]; then
        inc_status
      fi
      ;;
    1) 
      result=`wget --no-check-certificate --quiet -O - "$LIGHTHOUSE_BASE_URL/eth/v2/beacon/blocks/head" | jq -r '.data.message.slot'`
      if [ ! -z "$result" ] && [ $result -gt 0 ]; then
        inc_status
      fi
      ;;
    2)
      result=`wget --no-check-certificate --quiet -O - "$LIGHTHOUSE_BASE_URL/eth/v2/beacon/blocks/head" | jq -r '.version'`
      if [ ! -z "$result" ] && ([ "$result" == "altair" ] || [ "$result" == "bellatrix" ]); then
        inc_status
      fi
      ;;
    3)
      result=`wget --no-check-certificate --quiet -O - "$LIGHTHOUSE_BASE_URL/eth/v2/beacon/blocks/head" | jq -r '.version'`
      if [ ! -z "$result" ] && [ "$result" == "bellatrix" ]; then
        inc_status
      fi
      ;;
    4)
      result=`wget --no-check-certificate --quiet -O - "$LIGHTHOUSE_BASE_URL/eth/v2/beacon/blocks/head" | jq -r '.data.message.body.execution_payload.block_number'`
      if [ ! -z "$result" ] && [ $result -gt 0 ]; then
        inc_status
      fi
      ;;
  esac
done
