FROM node:18.17.1-alpine3.18

RUN apk --update --no-cache add python3 alpine-sdk bash curl jq

WORKDIR /app

COPY . .

RUN echo "Installing dependencies" && \
  yarn

WORKDIR /app/packages/nitro-util
