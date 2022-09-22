FROM node:16.13.1-alpine3.14

ARG NPM_AUTH_TOKEN
WORKDIR /app

COPY . .

RUN echo //npm.pkg.github.com/:_authToken=$NPM_AUTH_TOKEN > ~/.npmrc

RUN apk --update --no-cache add git && yarn
