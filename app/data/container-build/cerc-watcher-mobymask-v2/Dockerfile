FROM ubuntu:22.04

RUN apt-get update \
  && apt-get install -y curl gnupg build-essential \
  && curl --silent --location https://deb.nodesource.com/setup_18.x | bash - \
  && apt-get update \
  && apt-get install -y nodejs git busybox \
  && node -v

RUN corepack enable \
  && yarn --version

WORKDIR /app

COPY . .

RUN echo "Building watcher-ts" && \
    yarn && yarn build

WORKDIR /app/packages/mobymask-v2-watcher
