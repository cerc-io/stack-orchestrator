FROM ethpandaops/ethereum-genesis-generator:3.0.0 AS ethgen

FROM golang:1.20-alpine as builder

RUN apk add --no-cache python3 py3-pip make bash envsubst jq

# Install ethereum-genesis-generator tools
COPY --from=ethgen /apps /apps
RUN cd /apps/el-gen && pip3 install --break-system-packages -r requirements.txt
RUN pip3 install --break-system-packages --upgrade "web3==v6.15.1"
RUN pip3 install --break-system-packages --upgrade "typing-extensions"

# Install tool to generate initial block
RUN go install github.com/cerc-io/eth-dump-genblock@b29516740fc01cf1d1d623acbfd0e9a2b6440a96

# Build genesis config
COPY genesis /opt/genesis
RUN cd /opt/genesis && make genesis-el

# Snag the genesis block info.
RUN eth-dump-genblock /opt/genesis/build/el/geth.json > /opt/genesis/build/el/genesis_block.json

FROM alpine:latest

COPY --from=builder /opt/genesis /opt/genesis
