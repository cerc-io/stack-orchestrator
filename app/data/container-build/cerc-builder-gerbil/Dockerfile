# From: https://github.com/vyzo/gerbil/blob/master/docker/Dockerfile
FROM gerbil/ubuntu

# Install the Solidity compiler (latest stable version)
# and guile
# and libsecp256k1-dev
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && export DEBCONF_NOWARNINGS="yes" && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:ethereum/ethereum && \
    apt-get update && \
    apt-get install -y solc && \
    apt-get install -y guile-3.0 && \
    apt-get install -y libsecp256k1-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir /scripts
COPY install-dependencies.sh /scripts

# Override the definition of GERBIL_PATH in the base image, but
# is safe because (at present) no gerbil packages are installed in the base image
# We do this in order to allow a set of pre-installed packages from the container
# to be used with an arbitrary, potentially different set of projects bind mounted
# at /src
ENV GERBIL_PATH=/.gerbil
RUN bash /scripts/install-dependencies.sh

# Needed to prevent git from raging about /src
RUN git config --global --add safe.directory /src

COPY entrypoint.sh /scripts
ENTRYPOINT ["/scripts/entrypoint.sh"]
