#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# TODO: is there a better of passing user-defined variables for container build?
source ${CERC_REPO_BASE_DIR}/explorer/laconic-explorer.env
EXPLORER_DOMAIN=${EXPLORER_DOMAIN:-localhost}
EXPLORER_IP=${EXPLORER_IP:-127.0.0.1}
API_PORT=${API_PORT:-1317}
RPC_PORT=${RPC_PORT:-26657}

# Replace repo's Dockerfile with ours
cp ${SCRIPT_DIR}/../../config/laconic-explorer/Dockerfile ${CERC_REPO_BASE_DIR}/explorer/Dockerfile

# Remove all configs for other chains
rm -rf ${CERC_REPO_BASE_DIR}/explorer/src/chains/mainnet
mkdir -p ${CERC_REPO_BASE_DIR}/explorer/src/chains/mainnet
rm -rf ${CERC_REPO_BASE_DIR}/explorer/src/chains/testnet
mkdir -p ${CERC_REPO_BASE_DIR}/explorer/src/chains/testnet

if [ "${USE_HTTPS}" = "true" ]; then
  # Update laconic config with domain name, and copy to repo
  cat ${SCRIPT_DIR}/../../config/laconic-explorer/laconic.json | jq ".api[0]=\"https://api.${EXPLORER_DOMAIN}\" | .rpc[0]=\"https://rpc.${EXPLORER_DOMAIN}\"" > ${CERC_REPO_BASE_DIR}/explorer/src/chains/mainnet/laconic.json
  # Update nginx config with domain name, and copy to repo
  sed "s#DOMAIN#${EXPLORER_DOMAIN}#g" ${SCRIPT_DIR}/../../config/laconic-explorer/ping.conf.https > ${CERC_REPO_BASE_DIR}/explorer/ping.conf

else
  # Update laconic config with server IP and api/rpc ports, and copy to repo
  cat ${SCRIPT_DIR}/../../config/laconic-explorer/laconic.json | jq ".api[0]=\"http://${EXPLORER_IP}:${API_PORT}\" | .rpc[0]=\"http://${EXPLORER_IP}:${RPC_PORT}\"" > ${CERC_REPO_BASE_DIR}/explorer/src/chains/mainnet/laconic.json
  # Update nginx config to listen on specified api/rpc ports, and copy to repo
  sed "s#listen 1317#listen ${API_PORT}#; s#listen 26657#listen ${RPC_PORT}#" ${SCRIPT_DIR}/../../config/laconic-explorer/ping.conf.http > ${CERC_REPO_BASE_DIR}/explorer/ping.conf
fi

# Build cerc/laconic-explorer
docker build -t cerc/laconic-explorer:local ${CERC_REPO_BASE_DIR}/explorer

if [ "${USE_HTTPS}" = "true" ]; then
  echo "Explorer configured for https at domain ${EXPLORER_DOMAIN}. Please ensure ports 80 and 443 are accessible."
else
  echo "Explorer configured for http at IP ${EXPLORER_IP}. Please ensure ports 80, ${API_PORT} and ${RPC_PORT} are accessible."
fi