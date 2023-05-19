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
RUN geth --datadir ~/ethdata init /opt/testnet/build/el/geth.json && rm -f ~/ethdata/geth/nodekey

ENTRYPOINT ["/opt/testnet/run.sh"]
