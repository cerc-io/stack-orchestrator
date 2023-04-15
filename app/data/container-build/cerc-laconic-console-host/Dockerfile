# Originally from: https://github.com/devcontainers/images/blob/main/src/javascript-node/.devcontainer/Dockerfile
# [Choice] Node.js version (use -bullseye variants on local arm64/Apple Silicon): 18, 16, 14, 18-bullseye, 16-bullseye, 14-bullseye, 18-buster, 16-buster, 14-buster
ARG VARIANT=16-bullseye
FROM node:${VARIANT}

ARG USERNAME=node
ARG NPM_GLOBAL=/usr/local/share/npm-global

# This container pulls npm packages from a local registry configured via these env vars
ARG CERC_NPM_URL
ARG CERC_NPM_AUTH_TOKEN

# Add NPM global to PATH.
ENV PATH=${NPM_GLOBAL}/bin:${PATH}
# Prevents npm from printing version warnings
ENV NPM_CONFIG_UPDATE_NOTIFIER=false

RUN \
    # Configure global npm install location, use group to adapt to UID/GID changes
    if ! cat /etc/group | grep -e "^npm:" > /dev/null 2>&1; then groupadd -r npm; fi \
    && usermod -a -G npm ${USERNAME} \
    && umask 0002 \
    && mkdir -p ${NPM_GLOBAL} \
    && touch /usr/local/etc/npmrc \
    && chown ${USERNAME}:npm ${NPM_GLOBAL} /usr/local/etc/npmrc \
    && chmod g+s ${NPM_GLOBAL} \
    && npm config -g set prefix ${NPM_GLOBAL} \
    && su ${USERNAME} -c "npm config -g set prefix ${NPM_GLOBAL}" \
    # Install eslint
    && su ${USERNAME} -c "umask 0002 && npm install -g eslint" \
    && npm cache clean --force > /dev/null 2>&1

# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends jq

# [Optional] Uncomment if you want to install an additional version of node using nvm
# ARG EXTRA_NODE_VERSION=10
# RUN su node -c "source /usr/local/share/nvm/nvm.sh && nvm install ${EXTRA_NODE_VERSION}"

# We do this to get a yq binary from the published container, for the correct architecture we're building here
COPY --from=docker.io/mikefarah/yq:latest /usr/bin/yq /usr/local/bin/yq

RUN mkdir -p /scripts
COPY ./apply-webapp-config.sh /scripts
COPY ./start-serving-app.sh /scripts

# [Optional] Uncomment if you want to install more global node modules
# RUN su node -c "npm install -g <your-package-list-here>"

# Configure the local npm registry
RUN npm config set @cerc-io:registry ${CERC_NPM_URL} \
    && npm config set @lirewine:registry ${CERC_NPM_URL} \
    && npm config set -- ${CERC_NPM_URL}:_authToken ${CERC_NPM_AUTH_TOKEN}

RUN mkdir -p /config
COPY ./config.yml /config

# Install simple web server for now (use nginx perhaps later)
RUN yarn global add http-server

# Globally install the payload web app package
RUN yarn global add @cerc-io/console-app

# Expose port for http
EXPOSE 80

# Default command sleeps forever so docker doesn't kill it
CMD ["/scripts/start-serving-app.sh"]
