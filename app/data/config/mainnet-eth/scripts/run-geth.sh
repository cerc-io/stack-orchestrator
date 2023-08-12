#!/bin/sh
if [[ "true" == "$CERC_SCRIPT_DEBUG" ]]; then
    set -x
fi

START_CMD="geth"
if [[ "true" == "$CERC_REMOTE_DEBUG" ]] && [[ -x "/usr/local/bin/dlv" ]]; then
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
trap 'cleanup' SIGINT SIGTERM

MODE_FLAGS=""
if [[ "$CERC_GETH_MODE_QUICK_SET" = "archive" ]]; then
  MODE_FLAGS="--syncmode=${GETH_SYNC_MODE:-full} --gcmode=${GETH_GC_MODE:-archive} --snapshot=${GETH_SNAPSHOT:-false}"
else
  MODE_FLAGS="--syncmode=${GETH_SYNC_MODE:-snap} --gcmode=${GETH_GC_MODE:-full} --snapshot=${GETH_SNAPSHOT:-true}"
fi

$START_CMD \
  $MODE_FLAGS \
  --datadir="${GETH_DATA}"\
  --identity="${GETH_NODE_NAME}" \
  --maxpeers=${GETH_MAX_PEERS} \
  --cache=${GETH_CACHE} \
  --cache.gc=${GETH_CACHE_GC} \
  --cache.database=${GETH_CACHE_DB} \
  --cache.trie=${GETH_CACHE_TRIE} \
  --authrpc.addr='0.0.0.0' \
  --authrpc.vhosts='*'  \
  --authrpc.jwtsecret="${GETH_JWTSECRET}" \
  --http \
  --http.addr='0.0.0.0' \
  --http.api="${GETH_HTTP_API}" \
  --http.vhosts='*' \
  --metrics \
  --metrics.addr='0.0.0.0' \
  --ws \
  --ws.addr='0.0.0.0' \
  --ws.api="${GETH_WS_API}" \
  --rpc.gascap=${GETH_RPC_GASCAP} \
  --rpc.evmtimeout=${GETH_RPC_EVMTIMEOUT} \
  --txlookuplimit=${GETH_TXLOOKUPLIMIT}
  --verbosity=${GETH_VERBOSITY} \
  --log.vmodule="${GETH_VMODULE}" \
  ${GETH_OPTS} &

geth_pid=$!
wait $geth_pid

if [ "true" == "$CERC_KEEP_RUNNING_AFTER_GETH_EXIT" ]; then
  while [ 1 -eq 1 ]; do
    sleep 60
  done
fi
