#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi


if [ -f /geth-accounts/accounts.csv ]; then
  echo "Using L1 private key from the mounted volume"
  # Read the private key of L1 account to deploy contract
  PRIVATE_KEY_DEPLOYER=$(head -n 1 /geth-accounts/accounts.csv | cut -d ',' -f 3)
else
  echo "Using PRIVATE_KEY_DEPLOYER from env"
fi

# Set the private key
jq --arg privateKey "$PRIVATE_KEY_DEPLOYER" '.privateKey = $privateKey' secrets-template.json > secrets.json

export L2_GETH_URL="http://${L2_GETH_HOST}:${L2_GETH_PORT}"
jq --arg rpcUrl "$L2_GETH_URL" '.rpcUrl = $rpcUrl' secrets.json > secrets_updated.json && mv secrets_updated.json secrets.json

npm start
