FROM node:18.17.1-alpine3.18

RUN apk --update --no-cache add git python3 alpine-sdk bash curl jq

WORKDIR /app

COPY . .

RUN echo "Installing dependencies and building ajna-watcher-ts" && \
  yarn && yarn build
