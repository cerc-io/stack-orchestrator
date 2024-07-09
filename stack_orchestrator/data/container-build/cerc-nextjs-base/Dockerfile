# Originally from: https://github.com/devcontainers/images/blob/main/src/javascript-node/.devcontainer/Dockerfile
# [Choice] Node.js version (use -bullseye variants on local arm64/Apple Silicon): 18, 16, 14, 18-bullseye, 16-bullseye, 14-bullseye, 18-buster, 16-buster, 14-buster
ARG VARIANT=20-bullseye-slim
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
    # Install semver
    && su ${USERNAME} -c "umask 0002 && npm install -g semver" \
    # Install pnpm
    && su ${USERNAME} -c "umask 0002 && npm install -g pnpm" \
    # Install bun
    && su ${USERNAME} -c "umask 0002 && npm install -g bun@1.1.x" \
    && npm cache clean --force > /dev/null 2>&1

# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends jq gettext-base procps

# [Optional] Uncomment if you want to install more global node modules
# RUN su node -c "npm install -g <your-package-list-here>"

# We do this to get a yq binary from the published container, for the correct architecture we're building here
COPY --from=docker.io/mikefarah/yq:latest /usr/bin/yq /usr/local/bin/yq

# Expose port for http
EXPOSE 80

COPY /scripts /scripts

# Default command sleeps forever so docker doesn't kill it
ENTRYPOINT ["/scripts/start-serving-app.sh"]
