FROM cerc/webapp-base:local

# This container pulls npm packages from a local registry configured via these env vars
ARG CERC_NPM_REGISTRY_URL
ARG CERC_NPM_AUTH_TOKEN

# Configure the local npm registry
RUN npm config set @cerc-io:registry ${CERC_NPM_REGISTRY_URL} \
    && npm config set @lirewine:registry ${CERC_NPM_REGISTRY_URL} \
    && npm config set -- ${CERC_NPM_REGISTRY_URL}:_authToken ${CERC_NPM_AUTH_TOKEN}

# Globally install the payload web app package
RUN yarn global add @cerc-io/console-app

COPY ./config.yml /config
