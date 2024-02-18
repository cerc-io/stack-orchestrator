FROM cerc/foundry:local

# Install node (local foundry is a debian based image)
RUN apt-get update \
  && apt-get install -y curl wget \
  && apt-get install -y git busybox jq python3 make gcc g++

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash \
  && export NVM_DIR="$HOME/.nvm" \
  &&  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" \
  && nvm install 16.16.0 \
  && node -v

SHELL ["/bin/bash", "-c"]
RUN source $HOME/.bashrc \
  && corepack enable \
  && yarn --version

WORKDIR /app

# Copy optimism repo contents
COPY . .

SHELL ["/bin/bash", "-c"]
RUN source $HOME/.bashrc \
  && echo "Building optimism" \
  && pnpm i -g pnpm@8.15.3 \
  && pnpm install && pnpm build

WORKDIR /app/packages/contracts-bedrock
