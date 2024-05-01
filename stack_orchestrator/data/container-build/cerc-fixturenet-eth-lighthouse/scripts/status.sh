#!/usr/bin/env bash
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

MIN_BLOCK_NUM=${1:-${MIN_BLOCK_NUM:-3}}
STATUSES=(
  "geth to generate DAG"
  "beacon phase0"
  "beacon altair"
  "beacon bellatrix pre-merge"
  "beacon post-merge"
  "block number $MIN_BLOCK_NUM"
)
STATUS=0

LIGHTHOUSE_BASE_URL=${LIGHTHOUSE_BASE_URL}
GETH_BASE_URL=${GETH_BASE_URL}

# TODO: Docker commands below should be replaced by some interface into stack orchestrator
# or some execution environment-neutral mechanism.
if [ -z "$LIGHTHOUSE_BASE_URL" ]; then
  LIGHTHOUSE_CONTAINER=`docker ps -q -f "name=fixturenet-eth-lighthouse-1-1"`
  if [ -z "$LIGHTHOUSE_CONTAINER" ]; then
    echo "Lighthouse container not found." 1>&2
    exit 1
  fi
  LIGHTHOUSE_PORT=`docker port $LIGHTHOUSE_CONTAINER 8001 | cut -d':' -f2`
  LIGHTHOUSE_BASE_URL="http://localhost:${LIGHTHOUSE_PORT}"
fi

if [ -z "$GETH_BASE_URL" ]; then
  GETH_CONTAINER=`docker ps -q -f "name=fixturenet-eth-geth-1-1"`
  if [ -z "$GETH_CONTAINER" ]; then
    echo "Lighthouse container not found." 1>&2
    exit 1
  fi
  GETH_PORT=`docker port $GETH_CONTAINER 8545 | cut -d':' -f2`
  GETH_BASE_URL="http://localhost:${GETH_PORT}"
fi

MARKER="."

function inc_status() {
  echo " done"
  STATUS=$((STATUS + 1))
  if [ $STATUS -lt ${#STATUSES[@]} ]; then
    echo -n "Waiting for ${STATUSES[$STATUS]}..."
  fi
}

echo -n "Waiting for ${STATUSES[$STATUS]}..."
while [ $STATUS -lt ${#STATUSES[@]} ]; do
  sleep 1
  echo -n "$MARKER"
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
      if [ ! -z "$result" ] && ([ "$result" == "altair" ] || [ "$result" == "bellatrix" ] || [ "$result" == "capella" ] || [ "$result" == "deneb" ]); then
        inc_status
      fi
      ;;
    3)
      result=`wget --no-check-certificate --quiet -O - "$LIGHTHOUSE_BASE_URL/eth/v2/beacon/blocks/head" | jq -r '.version'`
      if [ ! -z "$result" ] && ([ "$result" == "bellatrix" ] || [ "$result" == "capella" ] || [ "$result" == "deneb" ]); then
        inc_status
      fi
      ;;
    4)
      result=`wget --no-check-certificate --quiet -O - "$LIGHTHOUSE_BASE_URL/eth/v2/beacon/blocks/head" | jq -r '.data.message.body.execution_payload.block_number'`
      if [ ! -z "$result" ] && [ $result -gt 0 ]; then
        inc_status
      fi
      ;;
    5)
      result=`wget --no-check-certificate --quiet -O - "$LIGHTHOUSE_BASE_URL/eth/v2/beacon/blocks/head" | jq -r '.data.message.body.execution_payload.block_number'`
      if [ ! -z "$result" ] && [ $result -gt $MIN_BLOCK_NUM ]; then
        inc_status
      else
        MARKER="$result "
      fi
      ;;
  esac
done
