#!/bin/bash

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

ETHERBASE=`cat /opt/testnet/build/el/accounts.csv | head -1 | cut -d',' -f2`
NETWORK_ID=`cat /opt/testnet/el/el-config.yaml | grep 'chain_id' | awk '{ print $2 }'`
NETRESTRICT=`ip addr | grep inet | grep -v '127.0' | awk '{print $2}'`
CERC_ETH_DATADIR="${CERC_ETH_DATADIR:-$HOME/ethdata}"
CERC_PLUGINS_DIR="${CERC_PLUGINS_DIR:-/usr/local/lib/plugeth}"

cd /opt/testnet/build/el
python3 -m http.server 9898 &
cd $HOME

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
trap 'cleanup' SIGINT SIGTERM

if [ "true" == "$RUN_BOOTNODE" ]; then
    $START_CMD \
      --datadir="${CERC_ETH_DATADIR}" \
      --nodekeyhex="${BOOTNODE_KEY}" \
      --nodiscover \
      --ipcdisable \
      --networkid=${NETWORK_ID} \
      --netrestrict="${NETRESTRICT}" \
      &

    geth_pid=$!
else
    cd /opt/testnet/accounts
    ./import_keys.sh

    echo -n "$JWT" > /opt/testnet/build/el/jwtsecret

    if [ "$CERC_RUN_STATEDIFF" == "detect" ] && [ -n "$CERC_STATEDIFF_DB_HOST" ]; then
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
    if [ "$CERC_RUN_STATEDIFF" == "true" ]; then
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
          if [ $result -ge $CERC_STATEDIFF_DB_GOOSE_MIN_VER ]; then
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
      --statediff.waitforsync=true \
      --statediff.workers=${CERC_STATEDIFF_WORKERS:-1} \
      --statediff.writing=true"

      if [ -d "${CERC_PLUGINS_DIR}" ]; then
        # With plugeth, we separate the statediff options by prefixing with ' -- '
        STATEDIFF_OPTS="--pluginsdir "${CERC_PLUGINS_DIR}" -- ${STATEDIFF_OPTS}"
      fi
    fi

    $START_CMD \
      --datadir="${CERC_ETH_DATADIR}" \
      --bootnodes="${ENODE}" \
      --allow-insecure-unlock \
      --http \
      --http.addr="0.0.0.0" \
      --http.vhosts="*" \
      --http.api="${CERC_GETH_HTTP_APIS:-eth,web3,net,admin,personal,debug,statediff}" \
      --http.corsdomain="*" \
      --authrpc.addr="0.0.0.0" \
      --authrpc.vhosts="*" \
      --authrpc.jwtsecret="/opt/testnet/build/el/jwtsecret" \
      --ws \
      --ws.addr="0.0.0.0" \
      --ws.origins="*" \
      --ws.api="${CERC_GETH_WS_APIS:-eth,web3,net,admin,personal,debug,statediff}" \
      --http.corsdomain="*" \
      --networkid="${NETWORK_ID}" \
      --netrestrict="${NETRESTRICT}" \
      --gcmode archive \
      --txlookuplimit=0 \
      --cache.preimages \
      --syncmode=full \
      --mine \
      --miner.threads=1 \
      --metrics \
      --metrics.addr="0.0.0.0" \
      --verbosity=${CERC_GETH_VERBOSITY:-3} \
      --log.vmodule="${CERC_GETH_VMODULE:-statediff/*=5}" \
      --miner.etherbase="${ETHERBASE}" \
      ${STATEDIFF_OPTS} \
      &

    geth_pid=$!
fi

wait $geth_pid

if [ "true" == "$CERC_KEEP_RUNNING_AFTER_GETH_EXIT" ]; then
  while [ 1 -eq 1 ]; do
    sleep 60
  done
fi
