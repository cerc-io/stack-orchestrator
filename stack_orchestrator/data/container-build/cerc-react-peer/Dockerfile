FROM node:18.15.0-alpine3.16

# This container pulls npm package from a registry configured via env var
ARG CERC_NPM_REGISTRY_URL

RUN apk --update --no-cache add make git python3 jq bash

# We do this to get a yq binary from the published container, for the correct architecture we're building here
COPY --from=docker.io/mikefarah/yq:latest /usr/bin/yq /usr/local/bin/yq

RUN mkdir -p /scripts
COPY ./apply-webapp-config.sh /scripts
COPY ./start-serving-app.sh /scripts

# Configure the local npm registry
RUN npm config set @cerc-io:registry ${CERC_NPM_REGISTRY_URL}

RUN mkdir -p /config

# Install simple web server for now (use nginx perhaps later)
RUN yarn global add http-server

# Globally install the payload web app package
RUN yarn global add @cerc-io/test-app@0.2.34

# Expose port for http
EXPOSE 80

CMD ["/scripts/start-serving-app.sh"]
