FROM node:18.17.1-alpine3.18

RUN apk --update --no-cache add python3 alpine-sdk bash curl jq

WORKDIR /app

COPY packages/nitro-rpc-client  .

RUN echo "Installing dependencies" && \
  yarn

RUN yarn build
RUN ln -s /app/bin/nitro-rpc-client.js /bin/nitro-rpc-client
