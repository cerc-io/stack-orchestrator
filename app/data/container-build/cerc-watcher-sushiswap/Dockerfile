FROM node:18.15.0-alpine3.16

RUN apk --update --no-cache add git python3 alpine-sdk bash

WORKDIR /app

COPY . .

RUN echo "Building uniswap-watcher-ts" && \
  yarn && yarn build && yarn build:contracts
