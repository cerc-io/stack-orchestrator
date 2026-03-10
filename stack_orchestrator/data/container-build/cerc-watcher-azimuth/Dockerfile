FROM node:18.16.0-alpine3.16

RUN apk --update --no-cache add git python3 alpine-sdk jq

WORKDIR /app

COPY . .

# Get the latest Git commit hash and set it in package.json of all watchers
RUN COMMIT_HASH=$(git rev-parse HEAD) && \
    find . -name 'package.json' -exec sh -c ' \
    for packageFile; do \
        jq --arg commitHash "$0" ".commitHash = \$commitHash" "$packageFile" > "$packageFile.tmp" && \
        mv "$packageFile.tmp" "$packageFile"; \
    done \
    ' "$COMMIT_HASH" {} \;

RUN echo "Building azimuth-watcher-ts" && \
    yarn && yarn build

RUN echo "Install toml-js to update watcher config files" && \
    yarn add --dev --ignore-workspace-root-check toml-js
