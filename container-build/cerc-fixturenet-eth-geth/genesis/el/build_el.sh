#!/usr/bin/env bash

# See: https://github.com/skylenet/ethereum-genesis-generator/blob/master/entrypoint.sh

rm -rf ../build/el
mkdir -p ../build/el

tmp_dir=$(mktemp -d -t ci-XXXXXXXXXX)
envsubst < el-config.yaml > $tmp_dir/genesis-config.yaml
python3 /apps/el-gen/genesis_geth.py $tmp_dir/genesis-config.yaml   > ../build/el/geth.json
python3 /apps/el-gen/genesis_chainspec.py $tmp_dir/genesis-config.yaml > ../build/el/chainspec.json
python3 /apps/el-gen/genesis_besu.py $tmp_dir/genesis-config.yaml > ../build/el/besu.json
