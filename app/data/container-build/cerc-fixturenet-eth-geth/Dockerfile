FROM skylenet/ethereum-genesis-generator@sha256:210353ce7c898686bc5092f16c61220a76d357f51eff9c451e9ad1b9ad03d4d3 AS ethgen

# Using the same golang image as used to build geth: https://github.com/cerc-io/go-ethereum/blob/HEAD/Dockerfile
FROM golang:1.18-alpine as delve
RUN go install github.com/go-delve/delve/cmd/dlv@latest

FROM cerc/go-ethereum:local as geth

FROM alpine:3.17
RUN apk add --no-cache python3 python3-dev py3-pip curl wget jq build-base gettext libintl openssl bash bind-tools postgresql-client

COPY --from=delve  /go/bin/dlv /usr/local/bin/
COPY --from=ethgen /usr/local/bin/eth2-testnet-genesis /usr/local/bin/
COPY --from=ethgen /usr/local/bin/eth2-val-tools /usr/local/bin/
COPY --from=ethgen /apps /apps

RUN cd /apps/el-gen && pip3 install -r requirements.txt

COPY genesis /opt/testnet
COPY run-el.sh /opt/testnet/run.sh

RUN cd /opt/testnet && make genesis-el

COPY --from=geth  /usr/local/bin/geth /usr/local/bin/

# Snag the genesis block info.
RUN geth --datadir ~/ethdata init /opt/testnet/build/el/geth.json && rm -f ~/ethdata/geth/nodekey
RUN cp -rp ~/ethdata ~/tmpeth && \
    geth --datadir ~/tmpeth init /opt/testnet/build/el/geth.json && \
    geth --datadir ~/tmpeth --http & \
    sleep 5 && \
    curl -q --location 'localhost:8545' \
        --header 'Content-Type: application/json' \
        --data '{ "jsonrpc": "2.0", "id": 14, "method": "eth_getBlockByNumber", "params": ["0x0", false] }' \
        -o /opt/testnet/build/el/genesis_block.json && \
    killall -9 geth && \
    rm -rf ~/tmpeth

ENTRYPOINT ["/opt/testnet/run.sh"]
