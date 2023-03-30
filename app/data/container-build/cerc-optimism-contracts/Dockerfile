FROM cerc/foundry:local

RUN apt-get update \
  && apt-get install -y curl \
  && curl --silent --location https://deb.nodesource.com/setup_16.x | bash - \
  && apt-get update \
  && apt-get install -y nodejs git busybox jq \
  && node -v

RUN corepack enable \
  && yarn --version

WORKDIR /app

COPY . .

RUN echo "Building optimism" && \
  yarn && yarn build

WORKDIR /app/packages/contracts-bedrock
