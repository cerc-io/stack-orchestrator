# copied and modified from erc20 Dockerfile

FROM node:16.17.1-alpine3.16

RUN apk --update --no-cache add git python3 alpine-sdk

WORKDIR /app

COPY . .

RUN echo "Building Laconic Explorer" && \
    git checkout master && \
    yarn && yarn build

#WORKDIR /app/packages/erc20-watcher
