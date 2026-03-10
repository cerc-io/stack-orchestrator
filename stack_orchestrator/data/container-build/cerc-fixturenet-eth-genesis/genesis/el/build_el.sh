#!/usr/bin/env bash
set -e

# See: https://github.com/skylenet/ethereum-genesis-generator/blob/master/entrypoint.sh

rm -rf ../build/el
mkdir -p ../build/el

tmp_dir=$(mktemp -d -t ci-XXXXXXXXXX)
envsubst < el-config.yaml > $tmp_dir/genesis-config.yaml

python3 /apps/el-gen/genesis_geth.py $tmp_dir/genesis-config.yaml | \
  jq 'del(.config.pragueTime)' \
  > ../build/el/geth.json

python3 ../accounts/mnemonic_to_csv.py $tmp_dir/genesis-config.yaml > ../build/el/accounts.csv
