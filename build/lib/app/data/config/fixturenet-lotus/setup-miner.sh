#!/bin/bash

lotus --version

nohup lotus daemon  --genesis=/devgen.car --profile=bootstrapper --bootstrap=false > /var/log/lotus.log 2>&1 &

# Loop until the daemon is started
echo "Waiting for daemon to start..."
while ! grep -q "started ChainNotify channel" /var/log/lotus.log ; do
    sleep 5
done
echo "Daemon started."

# if not already initialized
if [ ! -f /root/.lotus-shared/miner.addr ]; then
  # initialize miner
  lotus wallet import --as-default ~/.genesis-sectors/pre-seal-t01000.key
  lotus-miner init --genesis-miner --actor=t01000 --sector-size=2KiB --pre-sealed-sectors=~/.genesis-sectors --pre-sealed-metadata=~/.genesis-sectors/pre-seal-t01000.json --nosync
  
  # publish miner address to shared volume
  lotus net listen | awk 'NR==1{print}' > /root/.lotus-shared/miner.addr
fi

nohup lotus-miner run --nosync &

tail -f /dev/null
