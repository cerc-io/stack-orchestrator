# Note: cerc/foundry is Debian based
FROM cerc/foundry:local

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends jq curl netcat

WORKDIR /root

ARG GENESIS_FILE_PATH=genesis.json

COPY stateful ./stateful
COPY start-private-network.sh .
COPY deploy-local-network.sh .
COPY $GENESIS_FILE_PATH ./genesis.json
# TODO: figure out if this works for aarm64
COPY --from=cerc/go-ethereum:local /usr/local/bin/geth /bin/geth
RUN chmod +x /bin/geth

EXPOSE 8545
EXPOSE 8546
ENTRYPOINT ["./start-private-network.sh"]
