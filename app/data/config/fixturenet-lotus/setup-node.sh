#!/bin/bash

lotus --version

##TODO: paths can use values from lotus-env.env file

# Loop until the daemon is started
echo "Waiting for miner to share peering info..."
while [ ! -f /root/.lotus-shared/miner.addr ]; do
    sleep 5
done
echo "Resuming..."

# if not already initialized
if [ ! -f /root/.lotus-local-net/config.toml ]; then
  # init node config
  mkdir $HOME/.lotus-local-net
  lotus config default > $HOME/.lotus-local-net/config.toml

  # add bootstrap peer info if available
  if [ -f /root/.lotus-shared/miner.addr ]; then
    MINER_ADDR=\"$(cat /root/.lotus-shared/miner.addr)\"
    # add bootstrap peer id to config file
    sed -i "/^\[Libp2p\]/a \ \ BootstrapPeers = [$MINER_ADDR]" $HOME/.lotus-local-net/config.toml
  else
    echo "Bootstrap peer info not found, unable to configure. Manual peering will be required."
  fi
fi

# start node
lotus daemon --genesis=/devgen.car
