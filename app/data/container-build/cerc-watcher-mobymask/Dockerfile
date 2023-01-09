# TODO: move this into the cerc-io/mobymask-watcher repo
FROM node:16.17.1-alpine3.16

RUN apk --update --no-cache add git python3 alpine-sdk

WORKDIR /app

COPY . .

RUN echo "Building watcher-ts" && \
    git checkout v0.2.19 && \
    yarn && yarn build

WORKDIR /app/packages/mobymask-watcher
