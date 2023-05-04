FROM node:18.16.0-alpine3.16

RUN apk --update --no-cache add git python3 alpine-sdk

WORKDIR /app

COPY . .

RUN echo "Building azimuth-watcher-ts" && \
    yarn && yarn build

RUN echo "Install toml-js to update watcher config files" && \
    yarn add --dev toml-js
