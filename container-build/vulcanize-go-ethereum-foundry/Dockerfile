FROM ghcr.io/foundry-rs/foundry

RUN apk update ; apk add --no-cache --allow-untrusted ca-certificates curl bash git jq
RUN apk add --no-cache --upgrade grep
WORKDIR /root

ARG GENESIS_FILE_PATH=genesis.json

COPY stateful ./stateful
COPY start-private-network.sh .
COPY deploy-local-network.sh .
COPY $GENESIS_FILE_PATH ./genesis.json
# TODO: figure out if this works for aarm64
COPY --from=vulcanize/go-ethereum:local /usr/local/bin/geth /bin/geth
RUN chmod +x /bin/geth

EXPOSE 8545
EXPOSE 8546
ENTRYPOINT ["./start-private-network.sh"]
