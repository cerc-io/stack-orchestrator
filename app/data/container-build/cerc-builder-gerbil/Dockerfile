# From: https://github.com/vyzo/gerbil/blob/master/docker/Dockerfile
FROM gerbil/ubuntu

# Install the Solidity compiler (latest stable version)
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && export DEBCONF_NOWARNINGS="yes" && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:ethereum/ethereum && \
    apt-get update && apt-get install -y solc && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir /scripts
COPY install-dependencies.sh /scripts

RUN bash /scripts/install-dependencies.sh

# Needed to prevent git from raging about /src
RUN git config --global --add safe.directory /src

COPY entrypoint.sh /scripts
ENTRYPOINT ["/scripts/entrypoint.sh"]
