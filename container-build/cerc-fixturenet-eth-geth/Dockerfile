FROM skylenet/ethereum-genesis-generator@sha256:210353ce7c898686bc5092f16c61220a76d357f51eff9c451e9ad1b9ad03d4d3 AS ethgen

FROM cerc/go-ethereum:local
RUN apk add --no-cache python3 python3-dev py3-pip curl wget jq build-base gettext libintl openssl bash

COPY --from=ethgen /usr/local/bin/eth2-testnet-genesis /usr/local/bin/eth2-testnet-genesis
COPY --from=ethgen /usr/local/bin/eth2-val-tools /usr/local/bin/eth2-val-tools
COPY --from=ethgen /apps /apps

RUN cd /apps/el-gen && pip3 install -r requirements.txt

COPY genesis /opt/testnet
COPY run-el.sh /opt/testnet/run.sh

RUN cd /opt/testnet && make genesis-el

RUN geth init /opt/testnet/build/el/geth.json && rm -f ~/.ethereum/geth/nodekey

ENTRYPOINT ["/opt/testnet/run.sh"]
