#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "Running Nitro reverse payment proxy"
echo "Using CERC_PROXY_ADDRESS ${CERC_PROXY_ADDRESS}"
echo "Using CERC_PROXY_NITRO_ENDPOINT ${CERC_PROXY_NITRO_ENDPOINT}"
echo "Using CERC_PROXY_DESTINATION_URL ${CERC_PROXY_DESTINATION_URL}"
echo "Using CERC_PROXY_COST_PER_BYTE ${CERC_PROXY_COST_PER_BYTE}"

./proxy -proxyaddress ${CERC_PROXY_ADDRESS} -nitroendpoint=${CERC_PROXY_NITRO_ENDPOINT} -destinationurl=${CERC_PROXY_DESTINATION_URL} -costperbyte ${CERC_PROXY_COST_PER_BYTE} -enablepaidrpcmethods
