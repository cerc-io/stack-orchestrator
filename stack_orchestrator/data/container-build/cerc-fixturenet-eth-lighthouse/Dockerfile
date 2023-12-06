FROM cerc/lighthouse-cli:local AS lcli
FROM skylenet/ethereum-genesis-generator@sha256:210353ce7c898686bc5092f16c61220a76d357f51eff9c451e9ad1b9ad03d4d3 AS ethgen
FROM cerc/fixturenet-eth-genesis:local AS fnetgen

FROM cerc/lighthouse:local

# cerc/lighthouse is based on Ubuntu
RUN apt-get update && apt-get -y upgrade && apt-get install -y --no-install-recommends \
  libssl-dev ca-certificates \
  curl socat iproute2 telnet wget jq \
  build-essential python3 python3-dev python3-pip gettext-base \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY genesis /opt/testnet
COPY run-cl.sh /opt/testnet/run.sh

COPY --from=lcli /usr/local/bin/lcli /usr/local/bin/lcli
COPY --from=ethgen /usr/local/bin/eth2-testnet-genesis /usr/local/bin/eth2-testnet-genesis
COPY --from=ethgen /usr/local/bin/eth2-val-tools /usr/local/bin/eth2-val-tools
COPY --from=ethgen /apps /apps
COPY --from=fnetgen /opt/genesis/el /opt/testnet/el
COPY --from=fnetgen /opt/genesis/build/el /opt/testnet/build/el

RUN cd /opt/testnet && make genesis-cl

# Work around some bugs in lcli where the default path is always used.
RUN mkdir -p /root/.lighthouse && cd /root/.lighthouse && ln -s /opt/testnet/build/cl/testnet

RUN mkdir -p /scripts
COPY scripts/status-internal.sh /scripts
COPY scripts/status.sh /scripts

ENTRYPOINT ["/opt/testnet/run.sh"]
