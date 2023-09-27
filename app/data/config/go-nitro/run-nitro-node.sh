#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

NITRO_ADDRESSES_FILE_PATH="/app/deployment/nitro-addresses.json"

# Check if CERC_NA_ADDRESS environment variable set to skip contract deployment
if [ -n "$CERC_NA_ADDRESS" ]; then
  echo "CERC_NA_ADDRESS is set to '$CERC_NA_ADDRESS'"
  echo "CERC_VPA_ADDRESS is set to '$CERC_VPA_ADDRESS'"
  echo "CERC_CA_ADDRESS is set to '$CERC_CA_ADDRESS'"
  echo "Using the above Nitro addresses"

  NA_ADDRESS=${CERC_NA_ADDRESS}
  VPA_ADDRESS=${CERC_VPA_ADDRESS}
  CA_ADDRESS=${CERC_CA_ADDRESS}
elif [ -f ${NITRO_ADDRESSES_FILE_PATH} ]; then
  echo "Reading Nitro addresses from ${NITRO_ADDRESSES_FILE_PATH}"

  NA_ADDRESS=$(jq -r '.nitroAdjudicatorAddress' ${NITRO_ADDRESSES_FILE_PATH})
  VPA_ADDRESS=$(jq -r '.virtualPaymentAppAddress' ${NITRO_ADDRESSES_FILE_PATH})
  CA_ADDRESS=$(jq -r '.consensusAppAddress' ${NITRO_ADDRESSES_FILE_PATH})
else
  echo "${NITRO_ADDRESSES_FILE_PATH} not found"
  exit 1
fi

echo "Running Nitro node"

./nitro -chainurl ${NITRO_CHAIN_URL} -msgport ${NITRO_MSG_PORT} -rpcport ${NITRO_RPC_PORT} -wsmsgport ${NITRO_WS_MSG_PORT} -pk ${NITRO_PK} -chainpk ${NITRO_CHAIN_PK} -naaddress ${NA_ADDRESS} -vpaaddress ${VPA_ADDRESS} -caaddress ${CA_ADDRESS} -usedurablestore ${NITRO_USE_DURABLE_STORE} -durablestorefolder ${NITRO_DURABLE_STORE_FOLDER}
