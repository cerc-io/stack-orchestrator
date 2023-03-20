FROM node:18.15.0-alpine3.16

RUN apk --update --no-cache add make git

WORKDIR /app

COPY . .

RUN echo "Building react-peer" && \
    yarn && yarn workspace @cerc-io/react-peer build

WORKDIR /app
