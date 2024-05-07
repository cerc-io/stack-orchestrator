#####################################
FROM golang:1.21.7-bullseye AS lotus-builder
MAINTAINER Lotus Development Team

RUN apt-get update && apt-get install -y ca-certificates build-essential clang ocl-icd-opencl-dev ocl-icd-libopencl1 jq libhwloc-dev

ENV XDG_CACHE_HOME="/tmp"

### taken from https://github.com/rust-lang/docker-rust/blob/master/1.63.0/buster/Dockerfile
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH \
    RUST_VERSION=1.63.0

RUN set -eux; \
    dpkgArch="$(dpkg --print-architecture)"; \
    case "${dpkgArch##*-}" in \
        amd64) rustArch='x86_64-unknown-linux-gnu'; rustupSha256='5cc9ffd1026e82e7fb2eec2121ad71f4b0f044e88bca39207b3f6b769aaa799c' ;; \
        arm64) rustArch='aarch64-unknown-linux-gnu'; rustupSha256='e189948e396d47254103a49c987e7fb0e5dd8e34b200aa4481ecc4b8e41fb929' ;; \
        *) echo >&2 "unsupported architecture: ${dpkgArch}"; exit 1 ;; \
    esac; \
    url="https://static.rust-lang.org/rustup/archive/1.25.1/${rustArch}/rustup-init"; \
    wget "$url"; \
    echo "${rustupSha256} *rustup-init" | sha256sum -c -; \
    chmod +x rustup-init; \
    ./rustup-init -y --no-modify-path --profile minimal --default-toolchain $RUST_VERSION --default-host ${rustArch}; \
    rm rustup-init; \
    chmod -R a+w $RUSTUP_HOME $CARGO_HOME; \
    rustup --version; \
    cargo --version; \
    rustc --version;

COPY ./ /opt/filecoin
WORKDIR /opt/filecoin

ARG FFI_BUILD_FROM_SOURCE=0
ENV FFI_BUILD_FROM_SOURCE=${FFI_BUILD_FROM_SOURCE}

#RUN make clean deps

ARG RUSTFLAGS=""
ARG GOFLAGS=""

RUN make clean deps && \
    make lotus lotus-shed lotus-stats && \
    install -C ./lotus /usr/local/bin/lotus && \
    install -C ./lotus-shed /usr/local/bin/lotus-shed && \
    install -C ./lotus-stats /usr/local/bin/lotus-stats

#####################################
FROM ubuntu:20.04 AS lotus-base
MAINTAINER Lotus Development Team

# Base resources
COPY --from=lotus-builder /etc/ssl/certs                           /etc/ssl/certs
COPY --from=lotus-builder /lib/*/libdl.so.2         /lib/
COPY --from=lotus-builder /lib/*/librt.so.1         /lib/
COPY --from=lotus-builder /lib/*/libgcc_s.so.1      /lib/
COPY --from=lotus-builder /lib/*/libutil.so.1       /lib/
COPY --from=lotus-builder /usr/lib/*/libltdl.so.7   /lib/
COPY --from=lotus-builder /usr/lib/*/libnuma.so.1   /lib/
COPY --from=lotus-builder /usr/lib/*/libhwloc.so.*  /lib/
COPY --from=lotus-builder /usr/lib/*/libOpenCL.so.1 /lib/

RUN useradd -r -u 532 -U fc \
 && mkdir -p /etc/OpenCL/vendors \
 && echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd

#####################################
FROM lotus-base AS lotus
MAINTAINER Lotus Development Team

COPY --from=lotus-builder \
    /usr/local/bin/lotus \
    /usr/local/bin/lotus-shed \
    /usr/local/bin/

ENV FILECOIN_PARAMETER_CACHE /var/tmp/filecoin-proof-parameters
ENV LOTUS_PATH /var/lib/lotus
ENV DOCKER_LOTUS_IMPORT_WALLET ""

RUN mkdir /var/lib/lotus /var/tmp/filecoin-proof-parameters
RUN chown fc: /var/lib/lotus /var/tmp/filecoin-proof-parameters

VOLUME /var/lib/lotus
VOLUME /var/tmp/filecoin-proof-parameters

USER fc

EXPOSE 1234


CMD ["-help"]

#####################################
FROM lotus-base AS lotus-all-in-one

# Install netcat for healthcheck
RUN apt-get update && apt-get install -y netcat && apt-get install -y iproute2

ENV FILECOIN_PARAMETER_CACHE /var/tmp/filecoin-proof-parameters
ENV LOTUS_PATH /var/lib/lotus

ARG DOCKER_LOTUS_IMPORT_SNAPSHOT=https://forest-archive.chainsafe.dev/latest/mainnet/
ENV DOCKER_LOTUS_IMPORT_SNAPSHOT=${DOCKER_LOTUS_IMPORT_SNAPSHOT}

COPY --from=lotus-builder /opt/filecoin/lotus          /usr/local/bin/
COPY --from=lotus-builder /opt/filecoin/lotus-shed     /usr/local/bin/
COPY --from=lotus-builder /opt/filecoin/lotus-stats    /usr/local/bin/
COPY scripts/docker-lotus-entrypoint.sh /docker-lotus-entrypoint.sh
RUN chmod +x /docker-lotus-entrypoint.sh

RUN mkdir /var/tmp/filecoin-proof-parameters
RUN mkdir /var/lib/lotus
RUN chown fc: /var/tmp/filecoin-proof-parameters
RUN chown fc: /var/lib/lotus


VOLUME /var/tmp/filecoin-proof-parameters
VOLUME /var/lib/lotus

EXPOSE 1234
EXPOSE 1235

