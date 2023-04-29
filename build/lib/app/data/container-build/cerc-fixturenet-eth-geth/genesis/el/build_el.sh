#!/usr/bin/env bash
set -e

# See: https://github.com/skylenet/ethereum-genesis-generator/blob/master/entrypoint.sh

rm -rf ../build/el
mkdir -p ../build/el

tmp_dir=$(mktemp -d -t ci-XXXXXXXXXX)
envsubst < el-config.yaml > $tmp_dir/genesis-config.yaml

ttd=`cat $tmp_dir/genesis-config.yaml | grep terminal_total_difficulty | awk '{ print $2 }'`
homestead_block=`cat $tmp_dir/genesis-config.yaml | grep homestead_block | awk '{ print $2 }'`
eip150_block=`cat $tmp_dir/genesis-config.yaml | grep eip150_block | awk '{ print $2 }'`
eip155_block=`cat $tmp_dir/genesis-config.yaml | grep eip155_block | awk '{ print $2 }'`
eip158_block=`cat $tmp_dir/genesis-config.yaml | grep eip158_block | awk '{ print $2 }'`
byzantium_block=`cat $tmp_dir/genesis-config.yaml | grep byzantium_block | awk '{ print $2 }'`
constantinople_block=`cat $tmp_dir/genesis-config.yaml | grep constantinople_block | awk '{ print $2 }'`
petersburg_block=`cat $tmp_dir/genesis-config.yaml | grep petersburg_block | awk '{ print $2 }'`
istanbul_block=`cat $tmp_dir/genesis-config.yaml | grep istanbul_block | awk '{ print $2 }'`
berlin_block=`cat $tmp_dir/genesis-config.yaml | grep berlin_block | awk '{ print $2 }'`
london_block=`cat $tmp_dir/genesis-config.yaml | grep london_block | awk '{ print $2 }'`
merge_fork_block=`cat $tmp_dir/genesis-config.yaml | grep merge_fork_block | awk '{ print $2 }'`

python3 /apps/el-gen/genesis_geth.py $tmp_dir/genesis-config.yaml | \
  jq ".config.terminalTotalDifficulty=$ttd" | \
  jq ".config.homesteadBlock=$homestead_block" | \
  jq ".config.eip150Block=$eip150_block" | \
  jq ".config.eip155Block=$eip155_block" | \
  jq ".config.eip158Block=$eip158_block" | \
  jq ".config.byzantiumBlock=$byzantium_block" | \
  jq ".config.constantinopleBlock=$constantinople_block" | \
  jq ".config.petersburgBlock=$petersburg_block" | \
  jq ".config.istanbulBlock=$istanbul_block" | \
  jq ".config.berlinBlock=$berlin_block" | \
  jq ".config.londonBlock=$london_block" | \
  jq ".config.mergeForkBlock=$merge_fork_block" > ../build/el/geth.json
python3 ../accounts/mnemonic_to_csv.py $tmp_dir/genesis-config.yaml > ../build/el/accounts.csv
