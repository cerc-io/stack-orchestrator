#!/bin/bash

lotus --version

# # remove old bootnode peer info if present
# [ -f /root/.lotus-shared/miner.addr ] && rm /root/.lotus-shared/miner.addr

# start daemon
nohup lotus daemon  --genesis=/devgen.car --profile=bootstrapper --bootstrap=false > /var/log/lotus.log 2>&1 &

# Loop until the daemon is started
echo "Waiting for daemon to start..."
while ! grep -q "started ChainNotify channel" /var/log/lotus.log ; do
    sleep 5
done
echo "Daemon started."

# publish bootnode peer info to shared volume
lotus net listen | awk 'NR==1{print}' > /root/.lotus-shared/miner.addr

# if miner not already initialized
if [ ! -d /root/.lotus-miner-local-net ]; then
  # initialize miner
  lotus wallet import --as-default ~/.genesis-sectors/pre-seal-t01000.key
  lotus-miner init --genesis-miner --actor=t01000 --sector-size=2KiB --pre-sealed-sectors=~/.genesis-sectors --pre-sealed-metadata=~/.genesis-sectors/pre-seal-t01000.json --nosync
fi

# start miner
nohup lotus-miner run --nosync &

tail -f /dev/null
