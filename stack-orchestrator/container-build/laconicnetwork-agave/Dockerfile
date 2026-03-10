# Unified Agave/Jito Solana image
# Supports three modes via AGAVE_MODE env: test, rpc, validator
#
# Build args:
#   AGAVE_REPO    - git repo URL (anza-xyz/agave or jito-foundation/jito-solana)
#   AGAVE_VERSION - git tag to build (e.g. v3.1.9, v3.1.8-jito)

ARG AGAVE_REPO=https://github.com/anza-xyz/agave.git
ARG AGAVE_VERSION=v3.1.9

# ---------- Stage 1: Build ----------
FROM rust:1.85-bookworm AS builder

ARG AGAVE_REPO
ARG AGAVE_VERSION

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libssl-dev \
    libudev-dev \
    libclang-dev \
    protobuf-compiler \
    ca-certificates \
    git \
    cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone "$AGAVE_REPO" --depth 1 --branch "$AGAVE_VERSION" --recurse-submodules agave
WORKDIR /build/agave

# Cherry-pick --public-tvu-address support (anza-xyz/agave PR #6778, commit 9f4b3ae)
# This flag only exists on master, not in v3.1.9 — fetch the PR ref and cherry-pick
ARG TVU_ADDRESS_PR=6778
RUN if [ -n "$TVU_ADDRESS_PR" ]; then \
      git fetch --depth 50 origin "pull/${TVU_ADDRESS_PR}/head:tvu-pr" && \
      git cherry-pick --no-commit tvu-pr; \
    fi

# Build all binaries using the upstream install script
RUN CI_COMMIT=$(git rev-parse HEAD) scripts/cargo-install-all.sh /solana-release

# ---------- Stage 2: Runtime ----------
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libssl3 \
    libudev1 \
    curl \
    sudo \
    aria2 \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with sudo
RUN useradd -m -s /bin/bash agave \
    && echo "agave ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Copy all compiled binaries
COPY --from=builder /solana-release/bin/ /usr/local/bin/

# Copy entrypoint and support scripts
COPY entrypoint.py snapshot_download.py ip_echo_preflight.py /usr/local/bin/
COPY start-test.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.py /usr/local/bin/start-test.sh

# Create data directories
RUN mkdir -p /data/config /data/ledger /data/accounts /data/snapshots \
    && chown -R agave:agave /data

USER agave
WORKDIR /data

ENV RUST_LOG=info
ENV RUST_BACKTRACE=1

EXPOSE 8899 8900 8001 8001/udp

ENTRYPOINT ["entrypoint.py"]
