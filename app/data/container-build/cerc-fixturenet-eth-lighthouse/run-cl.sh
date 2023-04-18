#!/bin/bash

if [ "true" == "$RUN_BOOTNODE" ]; then
    cd /opt/testnet/build/cl
    python3 -m http.server 3000 &


    cd /opt/testnet/cl
    ./bootnode.sh 2>&1 | tee /var/log/lighthouse_bootnode.log
else
    while [ 1 -eq 1 ]; do
      echo "Waiting on geth ..."
      sleep 5
      result=`wget --no-check-certificate --quiet \
        -O - \
        --method POST \
        --timeout=0 \
        --header 'Content-Type: application/json' \
        --body-data '{ "jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": [] }' "${ETH1_ENDPOINT:-localhost:8545}" | jq -r '.result'`
       if [ ! -z "$result" ] && [ "null" != "$result" ]; then
           break
       fi
    done

    cd /opt/testnet/cl

    if [ -z "$LIGHTHOUSE_GENESIS_STATE_URL" ]; then
        # Check if beacon node data exists to avoid resetting genesis time on a restart
        if [ -d /opt/testnet/build/cl/node_"$NODE_NUMBER"/beacon ]; then
            echo "Skipping genesis time reset"
        else
            ./reset_genesis_time.sh
        fi
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

    if [ ! -z "$ENR_URL" ]; then
        while [ 1 -eq 1 ]; do
            echo "Waiting on ENR for boot node..."
            sleep 5
            result=`wget --no-check-certificate --quiet -O - --timeout=0 $ENR_URL`
            if [ ! -z "$result" ]; then
                export ENR="$result"
                break;
            fi
        done
    fi

    export JWTSECRET="/opt/testnet/build/cl/jwtsecret"
    echo -n "$JWT" > $JWTSECRET

    # See https://linuxconfig.org/how-to-propagate-a-signal-to-child-processes-from-a-bash-script
    cleanup() {
        echo "Signal received, cleaning up..."

        beacon_node_pid=$(pgrep -o -f 'lighthouse bn')
        validator_client_pid=$(pgrep -o -f 'lighthouse vc')

        kill ${beacon_node_pid}
        kill ${validator_client_pid}

        wait
        echo "Done"
    }
    trap 'cleanup' SIGINT SIGTERM

    ./beacon_node.sh 2>&1 | tee /var/log/lighthouse_bn.log &
    lpid=$!
    ./validator_client.sh 2>&1 | tee /var/log/lighthouse_vc.log &
    vpid=$!

    wait $lpid $vpid
fi

