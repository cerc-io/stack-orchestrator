FROM node:18.17.1-alpine3.18

RUN apk --update --no-cache add git python3 alpine-sdk bash curl jq

WORKDIR /app

COPY . .

# Get the latest Git commit hash and set in package.json
RUN COMMIT_HASH=$(git rev-parse HEAD) && \
  jq --arg commitHash "$COMMIT_HASH" '.commitHash = $commitHash' package.json > tmp.json && \
  mv tmp.json package.json

RUN echo "Installing dependencies and building ajna-watcher-ts" && \
  yarn && yarn build
