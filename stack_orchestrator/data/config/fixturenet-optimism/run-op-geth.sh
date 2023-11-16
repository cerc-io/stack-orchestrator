#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

l2_genesis_file="/l2-config/genesis.json"

# Check for genesis file; if necessary, wait on op-node to generate
timeout=300 # 5 minutes
start_time=$(date +%s)
elapsed_time=0
echo "Checking for L2 genesis file at location $l2_genesis_file"
while [ ! -f "$l2_genesis_file" ] && [ $elapsed_time -lt $timeout ]; do
  echo "Waiting for L2 genesis file to be generated..."
  sleep 10
  current_time=$(date +%s)
  elapsed_time=$((current_time - start_time))
done

if [ ! -f "$l2_genesis_file" ]; then
  echo "L2 genesis file not found after timeout of $timeout seconds. Exiting..."
  exit 1
fi

# Initialize geth from our generated L2 genesis file (if not already initialized)
data_dir="/datadir"
if [ ! -d "$datadir/geth" ]; then
  geth init --datadir=$data_dir $l2_genesis_file
fi

# Start op-geth
jwt_file="/l2-config/l2-jwt.txt"

geth \
  --datadir=$data_dir \
  --http \
  --http.corsdomain="*" \
  --http.vhosts="*" \
  --http.addr=0.0.0.0 \
  --http.api=web3,debug,eth,txpool,net,engine \
  --ws \
  --ws.addr=0.0.0.0 \
  --ws.port=8546 \
  --ws.origins="*" \
  --ws.api=debug,eth,txpool,net,engine \
  --syncmode=full \
  --gcmode=archive \
  --nodiscover \
  --maxpeers=0 \
  --networkid=42069 \
  --authrpc.vhosts="*" \
  --authrpc.addr=0.0.0.0 \
  --authrpc.port=8551 \
  --authrpc.jwtsecret=$jwt_file \
  --rollup.disabletxpoolgossip=true
