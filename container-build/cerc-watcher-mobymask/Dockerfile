# TODO: move this into the cerc-io/mobymask-watcher repo
FROM node:16.17.1-alpine3.16

RUN apk --update --no-cache add git python3 alpine-sdk

WORKDIR /app

COPY assemblyscript assemblyscript
COPY watcher-ts watcher-ts

# TODO: needs branch ng-integrate-asyncify
# TODO: why are we mixing npm and yarn below?
RUN echo "Building assemblyscript" && \
    cd assemblyscript && \
    npm install && npm run build && yarn link

# TODO: needs branch v0.2.13
RUN echo "Building watcher-ts" && \
    cd watcher-ts/packages/graph-node && yarn remove @vulcanize/assemblyscript && \
    yarn add https://github.com/vulcanize/assemblyscript.git#ng-integrate-asyncify && \
    cd ../../../watcher-ts && yarn && yarn link "@vulcanize/assemblyscript" && yarn build

WORKDIR /app/watcher-ts/packages/mobymask-watcher
