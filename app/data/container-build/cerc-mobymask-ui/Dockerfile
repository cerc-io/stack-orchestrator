FROM node:18.15.0-alpine3.16

RUN apk --update --no-cache add make git jq bash

WORKDIR /app

COPY . .

RUN npm install -g serve

RUN echo "Building mobymask-ui" && \
    npm install

WORKDIR /app
