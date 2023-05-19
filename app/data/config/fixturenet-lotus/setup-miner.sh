#!/bin/bash

lotus --version

# remove old bootnode peer info if present
if [ -f /root/.lotus-shared/miner.addr ]; then
  rm /root/.lotus-shared/miner.addr
fi


##TODO: generate genesis files inside container instead of bundling in config dir
##something like commands below should work, other scripts/compose will have to be updated to corresponding directories
# lotus fetch-params 2048
# lotus-seed pre-seal --sector-size 2KiB --num-sectors 2
# lotus-seed genesis new localnet.json
# lotus-seed genesis add-miner localnet.json ~/.genesis-sectors/pre-seal-t01000.json


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
