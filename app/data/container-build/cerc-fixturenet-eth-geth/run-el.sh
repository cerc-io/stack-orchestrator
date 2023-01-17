#!/bin/bash

ETHERBASE=`cat /opt/testnet/build/el/accounts.csv | head -1 | cut -d',' -f2`
NETWORK_ID=`cat /opt/testnet/el/el-config.yaml | grep 'chain_id' | awk '{ print $2 }'`
NETRESTRICT=`ip addr | grep inet | grep -v '127.0' | awk '{print $2}'`

HOME_DIR=`pwd`
cd /opt/testnet/build/el
python3 -m http.server 9898 &
cd $HOME_DIR

START_CMD="geth"
if [ "true" == "$CERC_REMOTE_DEBUG" ] && [ -x "/usr/local/bin/dlv" ]; then
    START_CMD="/usr/local/bin/dlv --listen=:40000 --headless=true --api-version=2 --accept-multiclient exec /usr/local/bin/geth --continue --"
fi

if [ "true" == "$RUN_BOOTNODE" ]; then
    $START_CMD \
      --nodekeyhex="${BOOTNODE_KEY}" \
      --nodiscover \
      --ipcdisable \
      --networkid=${NETWORK_ID} \
      --netrestrict="${NETRESTRICT}"
else
    cd /opt/testnet/accounts
    ./import_keys.sh
    
    echo -n "$JWT" > /opt/testnet/build/el/jwtsecret

    if [ "$CERC_RUN_STATEDIFF" == "detect" ] && [ -n "$CERC_STATEDIFF_DB_HOST" ]; then
      if [ -n "$(dig $CERC_STATEDIFF_DB_HOST +short)" ]; then
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
      while [ $ready -eq 0 ]; do
        echo "Waiting for statediff DB..."
        sleep 1
        export PGPASSWORD="$CERC_STATEDIFF_DB_PASSWORD"
        result=$(psql -h "$CERC_STATEDIFF_DB_HOST" \
          -p "$CERC_STATEDIFF_DB_PORT" \
          -U "$CERC_STATEDIFF_DB_USER" \
          -d "$CERC_STATEDIFF_DB_NAME" \
          -t -c 'select max(version_id) from goose_db_version;' 2>/dev/null | awk '{ print $1 }')
        if [ -n "$result" ] && [ $result -ge $CERC_STATEDIFF_DB_GOOSE_MIN_VER ]; then
          echo "DB ready..."
          ready=1
        fi
      done
      STATEDIFF_OPTS="--statediff=true \
      --statediff.db.host=$CERC_STATEDIFF_DB_HOST \
      --statediff.db.name=$CERC_STATEDIFF_DB_NAME \
      --statediff.db.nodeid=$CERC_STATEDIFF_DB_NODE_ID \
      --statediff.db.password=$CERC_STATEDIFF_DB_PASSWORD \
      --statediff.db.port=$CERC_STATEDIFF_DB_PORT \
      --statediff.db.user=$CERC_STATEDIFF_DB_USER \
      --statediff.db.logstatements=${CERC_STATEDIFF_DB_LOG_STATEMENTS:-false} \
      --statediff.waitforsync=true \
      --statediff.writing=true"
    fi

    $START_CMD \
      --bootnodes="${ENODE}" \
      --allow-insecure-unlock \
      --http \
      --http.addr="0.0.0.0" \
      --http.vhosts="*" \
      --http.api="eth,web3,net,admin,personal,debug,statediff" \
      --http.corsdomain="*" \
      --authrpc.addr="0.0.0.0" \
      --authrpc.vhosts="*" \
      --authrpc.jwtsecret="/opt/testnet/build/el/jwtsecret" \
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
      --vmodule="${CERC_GETH_VMODULE:-statediff/*=5}" \
      --miner.etherbase="${ETHERBASE}" ${STATEDIFF_OPTS}
fi
