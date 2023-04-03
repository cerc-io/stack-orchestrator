#!/bin/sh

# Assign deployed contract address from server config
CONTRACT_ADDRESS=$(jq -r '.address' /server/config.json | tr -d '"')
L1_PRIV_KEY_2=$(awk -F, 'NR==2{print $NF}' /geth-accounts/accounts.csv)

sed "s/REPLACE_WITH_PRIVATE_KEY/${L1_PRIV_KEY_2}/" environments/watcher-config-template.toml > environments/local.toml
sed -i "s/REPLACE_WITH_CONTRACT_ADDRESS/${CONTRACT_ADDRESS}/" environments/local.toml

echo 'yarn server'
yarn server
