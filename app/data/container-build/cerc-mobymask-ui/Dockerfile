# Originally from: https://github.com/devcontainers/images/blob/main/src/javascript-node/.devcontainer/Dockerfile
# [Choice] Node.js version (use -bullseye variants on local arm64/Apple Silicon): 18, 16, 14, 18-bullseye, 16-bullseye, 14-bullseye, 18-buster, 16-buster, 14-buster
ARG VARIANT=16-bullseye
FROM node:${VARIANT}

ARG USERNAME=node
ARG NPM_GLOBAL=/usr/local/share/npm-global

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

RUN mkdir -p /scripts

# Install simple web server for now (use nginx perhaps later)
RUN yarn global add http-server

WORKDIR /app
COPY . .
RUN npm install

# Expose port for http
EXPOSE 80
