#!/bin/sh

nitro_addresses_file="/app/deployment/nitro-addresses.json"

# Check if CERC_NA_ADDRESS environment variable is set
if [ -n "$CERC_NA_ADDRESS" ]; then
  echo "CERC_NA_ADDRESS is set to '$CERC_NA_ADDRESS'"
  echo "CERC_VPA_ADDRESS is set to '$CERC_VPA_ADDRESS'"
  echo "CERC_CA_ADDRESS is set to '$CERC_CA_ADDRESS'"
  echo "Using the above Nitro addresses"

  export NITRO_NA_ADDRESS=${CERC_NA_ADDRESS}
  export NITRO_VPA_ADDRESS=${CERC_VPA_ADDRESS}
  export NITRO_CA_ADDRESS=${CERC_CA_ADDRESS}
else
  # Read addresses from a file
  # Keep retrying until found
  echo "Reading Nitro addresses from ${nitro_addresses_file}"
  retry_interval=5
  while true; do
    if [[ -e "$nitro_addresses_file" ]]; then
      export NITRO_NA_ADDRESS=$(jq -r '.nitroAdjudicatorAddress' ${nitro_addresses_file})
      export NITRO_VPA_ADDRESS=$(jq -r '.virtualPaymentAppAddress' ${nitro_addresses_file})
      export NITRO_CA_ADDRESS=$(jq -r '.consensusAppAddress' ${nitro_addresses_file})

      break
    else
      echo "File not yet available, retrying in $retry_interval seconds..."
      sleep $retry_interval
    fi
  done
fi

# TODO: Wait for chain endpoint

echo "Beginning the ipld-eth-server process"

START_CMD="./ipld-eth-server"
if [ "true" == "$CERC_REMOTE_DEBUG" ] && [ -x "/usr/local/bin/dlv" ]; then
    START_CMD="/usr/local/bin/dlv --listen=:40000 --headless=true --api-version=2 --accept-multiclient exec `pwd`/ipld-eth-server --continue --"
fi

echo running: $START_CMD ${VDB_COMMAND} --config=`pwd`/config.toml
$START_CMD ${VDB_COMMAND} --config=`pwd`/config.toml
rv=$?

if [ $rv != 0 ]; then
  echo "ipld-eth-server startup failed"
  exit 1
fi
