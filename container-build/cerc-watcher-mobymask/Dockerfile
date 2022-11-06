# TODO: move this into the cerc-io/mobymask-watcher repo
FROM node:16.17.1-alpine3.16

WORKDIR /app

COPY . .

RUN apk --update --no-cache add git && yarn && yarn build
