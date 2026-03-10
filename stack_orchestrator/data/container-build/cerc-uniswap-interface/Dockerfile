FROM node:18.17.1-alpine3.18

RUN apk --update --no-cache add git make alpine-sdk bash

WORKDIR /app

COPY . .

RUN echo "Building uniswap-interface" && \
    yarn
