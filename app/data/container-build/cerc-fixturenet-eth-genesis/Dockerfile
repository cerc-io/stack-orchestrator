FROM skylenet/ethereum-genesis-generator@sha256:210353ce7c898686bc5092f16c61220a76d357f51eff9c451e9ad1b9ad03d4d3 AS ethgen

FROM golang:1.20-alpine as builder

RUN apk add --no-cache python3 py3-pip

COPY genesis /opt/genesis

# Install ethereum-genesis-generator tools
COPY --from=ethgen /usr/local/bin/eth2-testnet-genesis /usr/local/bin/
COPY --from=ethgen /usr/local/bin/eth2-val-tools /usr/local/bin/
COPY --from=ethgen /apps /apps
RUN cd /apps/el-gen && pip3 install -r requirements.txt
# web3==5.24.0 used by el-gen is broken on python 3.11
RUN pip3 install --upgrade "web3==6.5.0"

# Build genesis config
RUN apk add --no-cache make bash envsubst jq
RUN cd /opt/genesis && make genesis-el

# Snag the genesis block info.
RUN go install github.com/cerc-io/eth-dump-genblock@latest
RUN eth-dump-genblock /opt/genesis/build/el/geth.json > /opt/genesis/build/el/genesis_block.json

FROM alpine:latest

COPY --from=builder /opt/genesis /opt/genesis
