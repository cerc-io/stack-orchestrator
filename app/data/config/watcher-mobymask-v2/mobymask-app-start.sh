#!/bin/sh
set -e

# Merging config files to get deployed contract address
jq -s '.[0] * .[1]' /app/src/mobymask-app-config.json /server/config.json > /app/src/config.json

npm run build

serve -s build
