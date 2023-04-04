#!/bin/sh
set -e

# Read the private key of L1 account to deploy contract
# TODO: Take from env if /geth-accounts volume doesn't exist to allow using separately running L1
L1_PRIV_KEY=$(head -n 1 /geth-accounts/accounts.csv | cut -d ',' -f 3)

# Set the private key
jq --arg privateKey "$L1_PRIV_KEY" '.privateKey = $privateKey' secrets-template.json > secrets.json

export L2_GETH_URL="http://${L2_GETH_HOST}:${L2_GETH_PORT}"
jq --arg rpcUrl "$L2_GETH_URL" '.rpcUrl = $rpcUrl' secrets.json > secrets_updated.json && mv secrets_updated.json secrets.json

npm start
