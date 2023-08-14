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

# if genesis is not already setup
if [ ! -f /root/data/localnet.json ]; then
  lotus-seed --sector-dir /root/data/.genesis-sectors pre-seal --sector-size 2KiB --num-sectors 2
  lotus-seed --sector-dir /root/data/.genesis-sectors genesis new /root/data/localnet.json
  lotus-seed --sector-dir /root/data/.genesis-sectors genesis add-miner /root/data/localnet.json /root/data/.genesis-sectors/pre-seal-t01000.json
fi

# start daemon
# /root/.lotus-shared/devgen.car path
nohup lotus daemon --lotus-make-genesis=/root/.lotus-shared/devgen.car --profile=bootstrapper --genesis-template=/root/data/localnet.json --bootstrap=false > /var/log/lotus.log 2>&1 &

# Loop until the daemon is started
echo "Waiting for daemon to start..."
while ! grep -q "started ChainNotify channel" /var/log/lotus.log ; do
  sleep 5
done
echo "Daemon started."

# copy genesis file to shared volume
cp /devgen.car /root/.lotus-shared

# if miner not already initialized
if [ ! -d $LOTUS_MINER_PATH ]; then
  # initialize miner
  lotus wallet import --as-default /root/data/.genesis-sectors/pre-seal-t01000.key

  # fund a known account for usage
  /fund-account.sh

  lotus-miner init --genesis-miner --actor=t01000 --sector-size=2KiB --pre-sealed-sectors=/root/data/.genesis-sectors --pre-sealed-metadata=/root/data/.genesis-sectors/pre-seal-t01000.json --nosync
fi

# publish bootnode peer info to shared volume
lotus net listen | grep "$(ip addr | grep inet | grep -v '127.0.0.1' | sort | head -1 | awk '{print $2}' | cut -d '/' -f1)" | head -1 > /root/.lotus-shared/miner.addr

# start miner
nohup lotus-miner run --nosync &

tail -f /dev/null
