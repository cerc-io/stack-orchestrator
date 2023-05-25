FROM skylenet/ethereum-genesis-generator@sha256:210353ce7c898686bc5092f16c61220a76d357f51eff9c451e9ad1b9ad03d4d3 AS ethgen

FROM golang:1.19.4-bullseye AS delve
RUN go install github.com/go-delve/delve/cmd/dlv@latest

FROM ubuntu:22.04
RUN apt-get update && \
      apt-get install -y --no-install-recommends \
        python3 python3-dev python3-pip curl wget jq gettext gettext-base openssl bash dnsutils postgresql-client make iproute2 netcat && \
      rm -rf /var/lib/apt/lists/*

COPY --from=delve  /go/bin/dlv /usr/local/bin/
COPY --from=ethgen /usr/local/bin/eth2-testnet-genesis /usr/local/bin/
COPY --from=ethgen /usr/local/bin/eth2-val-tools /usr/local/bin/
COPY --from=ethgen /apps /apps

RUN wget -O /usr/local/bin/geth https://github.com/openrelayxyz/plugeth/releases/download/v1.11.6.1.0/geth-linux-amd64-v1.1.0-v1.11.6.1.0 && chmod a+x /usr/local/bin/geth
RUN cd /apps/el-gen && pip3 install -r requirements.txt

COPY genesis /opt/testnet
COPY run-el.sh /opt/testnet/run.sh

RUN cd /opt/testnet && make genesis-el

RUN geth --datadir ~/ethdata init /opt/testnet/build/el/geth.json && rm -f ~/ethdata/geth/nodekey

ENTRYPOINT ["/opt/testnet/run.sh"]
