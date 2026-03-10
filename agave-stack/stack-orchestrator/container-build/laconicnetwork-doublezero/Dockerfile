# DoubleZero network daemon for Solana validators
# Provides GRE tunnel + BGP routing via the DoubleZero fiber backbone

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Install DoubleZero from Cloudsmith apt repo
RUN curl -1sLf https://dl.cloudsmith.io/public/malbeclabs/doublezero/setup.deb.sh | bash \
    && apt-get update \
    && apt-get install -y doublezero \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
