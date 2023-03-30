#!/bin/sh

# Assign deployed contract address from server config
CONTRACT_ADDRESS=`jq '.address' /server/config.json`

sed "s/REPLACE_WITH_CONTRACT_ADDRESS/${CONTRACT_ADDRESS}/" environments/watcher-config-template.toml > environments/local.toml

echo 'yarn server'
yarn server
