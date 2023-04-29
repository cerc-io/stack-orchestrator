FROM node:16.17.1-alpine3.16

RUN apk --update --no-cache add git python3 alpine-sdk

WORKDIR /app

COPY . .

RUN echo "Building uniswap-watcher-ts" && \
    git checkout v0.3.4 && \
    yarn && yarn build && yarn build:contracts
