FROM cerc/foundry:local

# Install node (local foundry is a debian based image)
RUN apt-get update \
  && apt-get install -y curl wget \
  && curl --silent --location https://deb.nodesource.com/setup_16.x | bash - \
  && apt-get update \
  && apt-get install -y nodejs git busybox jq \
  && node -v

RUN corepack enable \
  && yarn --version

WORKDIR /app

# Copy optimism repo contents
COPY . .

RUN echo "Building optimism" && \
  yarn && yarn build

WORKDIR /app/packages/contracts-bedrock
