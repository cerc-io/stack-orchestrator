#!/bin/sh

# Assign deployed contract address from server config
CONTRACT_ADDRESS=$(jq -r '.address' /server/config.json | tr -d '"')
L1_PRIV_KEY_2=$(awk -F, 'NR==2{print $NF}' /geth-accounts/accounts.csv)

sed "s/REPLACE_WITH_PRIVATE_KEY/${L1_PRIV_KEY_2}/" environments/watcher-config-template.toml > environments/local.toml
sed -i "s/REPLACE_WITH_CONTRACT_ADDRESS/${CONTRACT_ADDRESS}/" environments/local.toml

export L2_GETH_URL="http://${L2_GETH_HOST}:${L2_GETH_PORT}"
sed -i "s/REPLACE_WITH_L2_GETH_URL/${L2_GETH_URL}/" environments/local.toml

echo 'yarn server'
yarn server
