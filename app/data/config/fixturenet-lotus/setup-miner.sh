#!/bin/bash

lotus --version

# remove old bootnode peer info if present
if [ -f /root/.lotus-shared/miner.addr ]; then
  rm /root/.lotus-shared/miner.addr
fi

# Check if filecoin-proof-parameters exist; avoid fetching if they do
if [ -z "$(find "/var/tmp/filecoin-proof-parameters" -maxdepth 1 -type f)" ]; then
  echo "Proof params not found, fetching..."
  lotus fetch-params 2048
else
  echo "Existing proof params found"
fi

lotus-seed pre-seal --sector-size 2KiB --num-sectors 2
lotus-seed genesis new localnet.json
lotus-seed genesis add-miner localnet.json ~/.genesis-sectors/pre-seal-t01000.json

# start daemon
nohup lotus daemon --lotus-make-genesis=devgen.car --profile=bootstrapper --genesis-template=localnet.json --bootstrap=false > /var/log/lotus.log 2>&1 &

# Loop until the daemon is started
echo "Waiting for daemon to start..."
while ! grep -q "started ChainNotify channel" /var/log/lotus.log ; do
    sleep 5
done
echo "Daemon started."

# copy genesis file to shared volume
cp /devgen.car /root/.lotus-shared

# publish bootnode peer info to shared volume
lotus net listen | awk 'NR==1{print}' > /root/.lotus-shared/miner.addr

# if miner not already initialized
if [ ! -d $LOTUS_MINER_PATH ]; then
  # initialize miner
  lotus wallet import --as-default ~/.genesis-sectors/pre-seal-t01000.key
  lotus-miner init --genesis-miner --actor=t01000 --sector-size=2KiB --pre-sealed-sectors=~/.genesis-sectors --pre-sealed-metadata=~/.genesis-sectors/pre-seal-t01000.json --nosync
fi

# start miner
nohup lotus-miner run --nosync &

tail -f /dev/null
