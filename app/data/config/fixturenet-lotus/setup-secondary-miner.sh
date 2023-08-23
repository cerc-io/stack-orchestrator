#!/bin/bash

lotus --version

# Wait for bootstrap peer info
echo "Waiting for miner 1 to share peering info..."
while [ ! -f /root/.lotus-shared/miner.addr ]; do
  sleep 5
done
echo "Resuming..."

# init node config
mkdir -p "$LOTUS_PATH"
lotus config default > "$LOTUS_PATH"/config.toml

# add bootstrap peer info to config file
MINER_ADDR=\"$(cat /root/.lotus-shared/miner.addr)\"
sed -i "/^\[Libp2p\]/a \ \ BootstrapPeers = [$MINER_ADDR]" $LOTUS_PATH/config.toml

# start node
nohup lotus daemon --genesis=/root/.lotus-shared/devgen.car > /var/log/lotus.log 2>&1 &

# Loop until the daemon is started
echo "Waiting for daemon to start..."
while ! grep -q "started ChainNotify channel" /var/log/lotus.log ; do
  sleep 5
done
echo "Daemon started."

# if miner not already initialized
if [ ! -d "$LOTUS_MINER_PATH" ]; then
  # initialize miner
  MINER_ACTOR="t0100$MINER_INDEX"

  lotus wallet import --as-default "/root/.lotus-shared/.genesis-sectors/pre-seal-$MINER_ACTOR.key"

  echo "Initializing miner..."
  lotus-miner init --actor="$MINER_ACTOR" --sector-size=2KiB --pre-sealed-sectors=/root/.lotus-shared/.genesis-sectors --pre-sealed-metadata=/root/.lotus-shared/.genesis-sectors/pre-seal-"$MINER_ACTOR".json --nosync
fi

# start miner
nohup lotus-miner run --nosync &

tail -f /dev/null
