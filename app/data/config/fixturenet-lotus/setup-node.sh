#!/bin/bash

lotus --version

# Loop until the daemon is started
echo "Waiting for miner to share peering info..."
while [ ! -f /root/.lotus-shared/miner.addr ]; do
  sleep 5
done
echo "Resuming..."

# init node config
mkdir -p $LOTUS_PATH
lotus config default > $LOTUS_PATH/config.toml

# add bootstrap peer info if available
if [ -f /root/.lotus-shared/miner.addr ]; then
  MINER_ADDR=\"$(cat /root/.lotus-shared/miner.addr)\"
  # add bootstrap peer id to config file
  sed -i "/^\[Libp2p\]/a \ \ BootstrapPeers = [$MINER_ADDR]" $LOTUS_PATH/config.toml
else
  echo "Bootstrap peer info not found, unable to configure. Manual peering will be required."
fi

# start node
lotus daemon --genesis=/root/.lotus-shared/devgen.car
