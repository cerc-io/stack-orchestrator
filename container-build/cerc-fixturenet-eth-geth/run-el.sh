#!/bin/bash

ETHERBASE=`cat /opt/testnet/build/el/accounts.csv | head -1 | cut -d',' -f2`
NETWORK_ID=`cat /opt/testnet/el/el-config.yaml | grep 'chain_id' | awk '{ print $2 }'`
NETRESTRICT=`ip addr | grep inet | grep -v '127.0' | awk '{print $2}'`

if [ "true" == "$RUN_BOOTNODE" ]; then 
    geth \
      --nodekeyhex="b0ac22adcad37213c7c565810a50f1772291e7b0ce53fb73e7ec2a3c75bc13b5" \
      --nodiscover \
      --ipcdisable \
      --networkid=${NETWORK_ID} \
      --netrestrict="${NETRESTRICT}"  2>&1 | tee /var/log/geth_bootnode.log
else
    cd /opt/testnet/accounts
    ./import_keys.sh
    
    echo -n "$JWT" > /opt/testnet/build/el/jwtsecret

    STATEDIFF_OPTS=""
    if [ "$RUN_STATEDIFF" == "true" ]; then
      STATEDIFF_OPTS="--statediff=true \
      --statediff.db.host=$STATEDIFF_DB_HOST \
      --statediff.db.name=$STATEDIFF_DB_NAME \
      --statediff.db.nodeid=$STATEDIFF_DB_NODE_ID \
      --statediff.db.password=$STATEDIFF_DB_PASSWORD \
      --statediff.db.port=$STATEDIFF_DB_PORT \
      --statediff.db.user=$STATEDIFF_DB_USER \
      --statediff.waitforsync=true \
      --statediff.writing=true"
    fi

    geth \
      --bootnodes="${ENODE}" \
      --allow-insecure-unlock \
      --http \
      --http.addr="0.0.0.0" \
      --http.vhosts="*" \
      --http.api="eth,web3,net,admin,personal" \
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
      --miner.etherbase="${ETHERBASE}" ${STATEDIFF_OPTS} 2>&1 | tee /var/log/geth.log
fi
