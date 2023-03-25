#!/bin/sh

# Private key of account with balance
PRIVATE_KEY=

# Assign deployed contract address from server config
CONTRACT_ADDRESS=`jq '.address' /server/config.json`

echo 'yarn peer-listener --contract-address <CONTRACT_ADDRESS> --private-key <PRIVATE_KEY>'
yarn peer-listener --contract-address $CONTRACT_ADDRESS --private-key $PRIVATE_KEY
