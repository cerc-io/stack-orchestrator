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

if [[ "${CERC_RUN_STATEDIFF}" == "detect" ]] && [[ -n "$CERC_STATEDIFF_DB_HOST" ]]; then
  dig_result=$(dig $CERC_STATEDIFF_DB_HOST +short)
  dig_status_code=$?
  if [[ $dig_status_code = 0 && -n $dig_result ]]; then
    echo "Statediff DB at $CERC_STATEDIFF_DB_HOST"
    CERC_RUN_STATEDIFF="true"
  else
    echo "No statediff DB available."
    CERC_RUN_STATEDIFF="false"
  fi
fi

STATEDIFF_OPTS=""
if [[ "${CERC_RUN_STATEDIFF}" == "true" ]]; then
  ready=0
  echo "Waiting for statediff DB..."
  while [ $ready -eq 0 ]; do
    sleep 1
    export PGPASSWORD="$CERC_STATEDIFF_DB_PASSWORD"
    result=$(psql -h "$CERC_STATEDIFF_DB_HOST" \
      -p "$CERC_STATEDIFF_DB_PORT" \
      -U "$CERC_STATEDIFF_DB_USER" \
      -d "$CERC_STATEDIFF_DB_NAME" \
      -t -c 'select max(version_id) from goose_db_version;' 2>/dev/null | awk '{ print $1 }')
    if [ -n "$result" ]; then
      echo "DB ready..."
      if [[ $result -ge $CERC_STATEDIFF_DB_GOOSE_MIN_VER ]]; then
        ready=1
      else
        echo "DB not at required version (want $CERC_STATEDIFF_DB_GOOSE_MIN_VER, have $result)"
      fi
    fi
  done

  STATEDIFF_OPTS="--statediff \
  --statediff.db.host=$CERC_STATEDIFF_DB_HOST \
  --statediff.db.name=$CERC_STATEDIFF_DB_NAME \
  --statediff.db.nodeid=$CERC_STATEDIFF_DB_NODE_ID \
  --statediff.db.password=$CERC_STATEDIFF_DB_PASSWORD \
  --statediff.db.port=$CERC_STATEDIFF_DB_PORT \
  --statediff.db.user=$CERC_STATEDIFF_DB_USER \
  --statediff.db.logstatements=${CERC_STATEDIFF_DB_LOG_STATEMENTS:-false} \
  --statediff.db.copyfrom=${CERC_STATEDIFF_DB_COPY_FROM:-true} \
  --statediff.waitforsync=${CERC_STATEDIFF_WAIT_FO_SYNC:-true} \
  --statediff.workers=${CERC_STATEDIFF_WORKERS:-1} \
  --statediff.writing=${CERC_STATEDIFF_WRITING:-true}"

  if [[ -d "${CERC_PLUGINS_DIR}" ]]; then
    # With plugeth, we separate the statediff options by prefixing with ' -- '
    STATEDIFF_OPTS="--pluginsdir "${CERC_PLUGINS_DIR}" -- ${STATEDIFF_OPTS}"
  fi
fi

$START_CMD \
  $MODE_FLAGS \
  --datadir="${GETH_DATADIR}"\
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
  --txlookuplimit=${GETH_TXLOOKUPLIMIT} \
  --verbosity=${GETH_VERBOSITY} \
  --log.vmodule="${GETH_VMODULE}" \
  ${STATEDIFF_OPTS} \
  ${GETH_OPTS} &

geth_pid=$!
wait $geth_pid

if [[ "true" == "$CERC_KEEP_RUNNING_AFTER_GETH_EXIT" ]]; then
  while [[ 1 -eq 1 ]]; do
    sleep 60
  done
fi
