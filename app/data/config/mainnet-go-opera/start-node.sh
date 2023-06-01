#!/bin/bash

# download genesis file
wget https://download.fantom.network/mainnet-109331-no-history.g

./opera --genesis=mainnet-109331-no-history.g --db.preset ldb-1 --syncmode snap --http --http.addr="0.0.0.0" --http.corsdomain="*" --http.api=eth,web3,net,txpool,ftm
#tail -f /dev/null
