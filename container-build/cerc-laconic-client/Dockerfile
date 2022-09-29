# TODO: move this into the cerc-io/laconic-sdk (aka client) repo
FROM node:16.17.1-alpine3.16

ARG NPM_AUTH_TOKEN
WORKDIR /app

COPY . .

RUN echo //npm.pkg.github.com/:_authToken=$NPM_AUTH_TOKEN > ~/.npmrc

RUN apk --update --no-cache add git && yarn && yarn build

ENTRYPOINT ["/app/bin/laconic"]
