FROM node:16.17.1-alpine3.16

RUN apk --update --no-cache add git python3 alpine-sdk jq

WORKDIR /app

COPY . .

RUN echo "Building watcher-ts" && \
    yarn && yarn build
