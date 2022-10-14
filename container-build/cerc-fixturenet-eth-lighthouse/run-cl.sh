#!/bin/bash

if [ "true" == "$RUN_BOOTNODE" ]; then 
    cd /opt/testnet/cl
    ./bootnode.sh 2>&1 | tee /var/log/lighthouse_bootnode.log
else
    while [ 1 -eq 1 ]; do
      echo "Waiting on DAG ..."
      sleep 5
      result=`wget --no-check-certificate --quiet \
        -O - \
        --method POST \
        --timeout=0 \
        --header 'Content-Type: application/json' \
        --body-data '{ "jsonrpc": "2.0", "id": 1, "method": "eth_getBlockByNumber", "params": ["0x3", false] }' "${ETH1_ENDPOINT:-localhost:8545}" | jq -r '.result'`
       if [ ! -z "$result" ] && [ "null" != "$result" ]; then
           break
       fi
    done

    cd /opt/testnet/cl

    if [ -z "$LIGHTHOUSE_GENESIS_STATE_URL" ]; then
        ./reset_genesis_time.sh
    else
        while [ 1 -eq 1 ]; do
            echo "Waiting on Genesis time ..."
            sleep 5
            result=`wget --no-check-certificate --quiet -O - --timeout=0 $LIGHTHOUSE_GENESIS_STATE_URL | jq -r '.data.genesis_time'`
            if [ ! -z "$result" ]; then
              ./reset_genesis_time.sh $result
              break;
            fi
        done
    fi

    export JWTSECRET="/opt/testnet/build/cl/jwtsecret"
    echo -n "$JWT" > $JWTSECRET

    ./beacon_node.sh 2>&1 | tee /var/log/lighthouse_bn.log &
    lpid=$!
    ./validator_client.sh 2>&1 | tee /var/log/lighthouse_vc.log &
    vpid=$!

    wait $lpid $vpid
fi

