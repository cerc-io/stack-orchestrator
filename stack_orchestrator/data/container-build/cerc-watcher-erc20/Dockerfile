FROM node:16.17.1-alpine3.16

RUN apk --update --no-cache add git python3 alpine-sdk bash curl jq

WORKDIR /app

COPY . .

RUN echo "Building erc20-watcher-ts" && \
    yarn && yarn build
