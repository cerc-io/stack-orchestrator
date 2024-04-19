#!/bin/bash

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

if [ -z "$CERC_NITRO_CHAIN_PK" ] || [ -z "$CERC_NITRO_CHAIN_URL" ]; then
  echo "You most set both CERC_NITRO_CHAIN_PK and CERC_NITRO_CHAIN_URL." 1>&2
  exit 1
fi

nitro_addresses_file="/app/deployment/nitro-addresses.json"

# Check if CERC_NA_ADDRESS environment variable is set
if [ -n "$CERC_NA_ADDRESS" ]; then
  echo "CERC_NA_ADDRESS is set to '$CERC_NA_ADDRESS'"
  echo "CERC_VPA_ADDRESS is set to '$CERC_VPA_ADDRESS'"
  echo "CERC_CA_ADDRESS is set to '$CERC_CA_ADDRESS'"
  echo "Using the above Nitro addresses"

  NA_ADDRESS=${CERC_NA_ADDRESS}
  VPA_ADDRESS=${CERC_VPA_ADDRESS}
  CA_ADDRESS=${CERC_CA_ADDRESS}
elif [ -f ${nitro_addresses_file} ]; then
  echo "Reading Nitro addresses from ${nitro_addresses_file}"

  NA_ADDRESS=$(jq -r '.nitroAdjudicatorAddress' ${nitro_addresses_file})
  VPA_ADDRESS=$(jq -r '.virtualPaymentAppAddress' ${nitro_addresses_file})
  CA_ADDRESS=$(jq -r '.consensusAppAddress' ${nitro_addresses_file})
else
  echo "File ${nitro_addresses_file} not found"
  exit 1
fi

cd /app/packages/example-web-app
cat > .env <<EOF
REACT_APP_RPC_URL=${CERC_RUNTIME_ENV_RPC_URL:-$CERC_NITRO_CHAIN_URL}
REACT_APP_TARGET_URL=${CERC_RUNTIME_ENV_TARGET_URL:-$CERC_NITRO_TARGET_URL}
REACT_APP_NITRO_PK=${CERC_NITRO_PK:-$CERC_NITRO_CHAIN_PK}
REACT_APP_NA_ADDRESS=${NA_ADDRESS}
REACT_APP_VPA_ADDRESS=${VPA_ADDRESS}
REACT_APP_CA_ADDRESS=${CA_ADDRESS}
EOF

yarn start