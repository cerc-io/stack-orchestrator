# Originally from: https://github.com/devcontainers/images/blob/main/src/javascript-node/.devcontainer/Dockerfile
# Which depends on: https://github.com/nodejs/docker-node/blob/main/Dockerfile-debian.template
# [Choice] Node.js version (use -bullseye variants on local arm64/Apple Silicon): 18, 16, 14, 18-bullseye, 16-bullseye, 14-bullseye, 18-buster, 16-buster, 14-buster
ARG VARIANT=18-bullseye
FROM node:${VARIANT}

# Set these args to change the uid/gid for the base container's "node" user to match that of the host user (so bind mounts work as expected).
ARG CERC_HOST_UID=1000
ARG CERC_HOST_GID=1000
# Make these values available at runtime to allow a consistency check.
ENV HOST_UID=${CERC_HOST_UID}
ENV HOST_GID=${CERC_HOST_GID}

ARG USERNAME=node
ARG NPM_GLOBAL=/usr/local/share/npm-global

# Add NPM global to PATH.
ENV PATH=${NPM_GLOBAL}/bin:${PATH}

RUN \
    if [ ${CERC_HOST_GID} -ne 1000 ] ; then \
        groupmod -g ${CERC_HOST_GID} ${USERNAME} ; \
    fi \
    && if [ ${CERC_HOST_UID} -ne 1000 ] ; then \
        usermod -u ${CERC_HOST_UID} -g ${CERC_HOST_GID} ${USERNAME} && chown ${CERC_HOST_UID}:${CERC_HOST_GID} /home/${USERNAME} ; \
    fi

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

# [Optional] Uncomment if you want to install more global node modules
# RUN su node -c "npm install -g <your-package-list-here>"

RUN mkdir /scripts
COPY build-npm-package.sh /scripts
COPY yarn-local-registry-fixup.sh /scripts
COPY build-npm-package-local-dependencies.sh /scripts
COPY check-uid.sh /scripts
ENV PATH="${PATH}:/scripts"

COPY entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
# Placeholder CMD : generally this will be overridden at run time like :
# docker run -it -v /home/builder/cerc/laconic-sdk:/workspace cerc/builder-js sh -c 'cd /workspace && yarn && yarn build'
CMD node --version
