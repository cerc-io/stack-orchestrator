FROM node:18.15.0-alpine3.16

ARG REPO_DIR

RUN apk --update --no-cache add make git jq bash

# We do this to get a yq binary from the published container, for the correct architecture we're building here
COPY --from=docker.io/mikefarah/yq:latest /usr/bin/yq /usr/local/bin/yq

RUN mkdir -p /scripts
COPY ./apply-webapp-config.sh /scripts
COPY ./start-serving-app.sh /scripts

RUN mkdir -p /config

# Install simple web server for now (use nginx perhaps later)
RUN yarn global add http-server

WORKDIR /app

# TODO: Workaround copying local repo outside docker build context
# Would not be required if publishing package for web-app build
RUN git clone --branch laconic https://github.com/cerc-io/mobymask-ui.git .

COPY ./mobymask-config.json /src/config.json

RUN echo "Building mobymask-ui"
RUN npm install
RUN REACT_APP_WATCHER_URI="MOBYMASK_HOSTED_CONFIG_watcherUrl/graphql" npm run build

WORKDIR /app

# Expose port for http
EXPOSE 80

CMD ["/scripts/start-serving-app.sh"]
