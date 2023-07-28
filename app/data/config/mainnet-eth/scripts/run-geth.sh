#!/bin/sh
if [[ -n "$CERC_SCRIPT_DEBUG" ]]; then
    set -x
fi

CERC_ETH_DATADIR=/root/ethdata

START_CMD="geth"
if [ "true" == "$CERC_REMOTE_DEBUG" ] && [ -x "/usr/local/bin/dlv" ]; then
    START_CMD="/usr/local/bin/dlv --listen=:40000 --headless=true --api-version=2 --accept-multiclient exec /usr/local/bin/geth --continue --"
fi

# See https://linuxconfig.org/how-to-propagate-a-signal-to-child-processes-from-a-bash-script
cleanup() {
    echo "Signal received, cleaning up..."

    # Kill the child process first (CERC_REMOTE_DEBUG=true uses dlv which starts geth as a child process)
    pkill -P ${geth_pid}
    sleep 2
    kill $(jobs -p)

    wait
    echo "Done"
}

$START_CMD \
    --datadir="${CERC_ETH_DATADIR}" \
    --authrpc.addr="0.0.0.0" \
    --authrpc.port 8551 \
    --authrpc.vhosts="*" \
    --authrpc.jwtsecret="/etc/mainnet-eth/jwtsecret" \
    --ws \
    --ws.addr="0.0.0.0" \
    --ws.origins="*" \
    --ws.api="${CERC_GETH_WS_APIS:-eth,web3,net,admin,personal,debug,statediff}" \
    --http.corsdomain="*" \
    --gcmode full \
    --txlookuplimit=0 \
    --cache.preimages \
    --syncmode=snap \
    &

geth_pid=$!


wait $geth_pid

if [ "true" == "$CERC_KEEP_RUNNING_AFTER_GETH_EXIT" ]; then
  while [ 1 -eq 1 ]; do
    sleep 60
  done
fi
