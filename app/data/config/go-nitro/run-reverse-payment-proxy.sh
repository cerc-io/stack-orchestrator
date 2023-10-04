#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "Running Nitro reverse payment proxy"
echo "Using PROXY_ADDRESS ${PROXY_ADDRESS}"
echo "Using PROXY_NITRO_ENDPOINT ${PROXY_NITRO_ENDPOINT}"
echo "Using PROXY_DESTINATION_URL ${PROXY_DESTINATION_URL}"
echo "Using PROXY_COST_PER_BYTE ${PROXY_COST_PER_BYTE}"

./proxy -proxyaddress ${PROXY_ADDRESS} -nitroendpoint=${PROXY_NITRO_ENDPOINT} -destinationurl=${PROXY_DESTINATION_URL} -costperbyte ${PROXY_COST_PER_BYTE} -enablepaidrpcmethods
