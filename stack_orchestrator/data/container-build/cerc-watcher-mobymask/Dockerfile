# TODO: move this into the cerc-io/mobymask-watcher repo
FROM node:18.17.1-alpine3.18

RUN apk --update --no-cache add git python3 alpine-sdk

WORKDIR /app

COPY . .

RUN echo "Building mobymask-watcher-ts" && \
    yarn && yarn build
