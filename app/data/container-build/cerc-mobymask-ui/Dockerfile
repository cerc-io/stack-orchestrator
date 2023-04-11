FROM node:18.15.0-alpine3.16

ARG REPO_DIR

RUN apk --update --no-cache add make git jq bash

RUN mkdir -p /scripts
COPY ../apply-webapp-config.sh /scripts
COPY ./start-serving-app.sh /scripts

# Install simple web server for now (use nginx perhaps later)
RUN yarn global add http-server

WORKDIR /app

COPY ${REPO_DIR} .

COPY ./mobymask-config.json /src/config.json

RUN echo "Building mobymask-ui" && \
    npm install && \
    REACT_APP_WATCHER_URI="MOBYMASK_HOSTED_CONFIG_watcherUrl/graphql" npm run build

WORKDIR /app

# Expose port for http
EXPOSE 80

CMD ["/scripts/start-serving-app.sh"]
