# Originally from: https://github.com/devcontainers/images/blob/main/src/javascript-node/.devcontainer/Dockerfile
# [Choice] Node.js version (use -bullseye variants on local arm64/Apple Silicon): 18, 16, 14, 18-bullseye, 16-bullseye, 14-bullseye, 18-buster, 16-buster, 14-buster
ARG VARIANT=16-bullseye
FROM node:${VARIANT}

ARG USERNAME=node
ARG NPM_GLOBAL=/usr/local/share/npm-global

# This container pulls npm package from a registry configured via env var
ARG CERC_NPM_REGISTRY_URL

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

# Install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends jq bash netcat

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

# Globally install both versions of the payload web app package
# Install old version of MobyMask web app
RUN yarn global add @cerc-io/mobymask-ui@0.1.4
# Install the LXDAO version of MobyMask web app
RUN yarn global add @cerc-io/mobymask-ui-lxdao@npm:@cerc-io/mobymask-ui@0.1.4-lxdao-0.1.1

# Expose port for http
EXPOSE 80

CMD ["/scripts/start-serving-app.sh"]
