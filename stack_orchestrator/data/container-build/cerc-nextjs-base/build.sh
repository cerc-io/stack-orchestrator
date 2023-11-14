#!/usr/bin/env bash
# Build cerc/laconic-registry-cli

source ${CERC_CONTAINER_BASE_DIR}/build-base.sh

# See: https://stackoverflow.com/a/246128/1701505
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

CERC_CONTAINER_BUILD_WORK_DIR=${CERC_CONTAINER_BUILD_WORK_DIR:-$SCRIPT_DIR}
CERC_CONTAINER_BUILD_DOCKERFILE=${CERC_CONTAINER_BUILD_DOCKERFILE:-$SCRIPT_DIR/Dockerfile}
CERC_CONTAINER_BUILD_TAG=${CERC_CONTAINER_BUILD_TAG:-cerc/nextjs-base:local}

docker build -t $CERC_CONTAINER_BUILD_TAG ${build_command_args} -f $CERC_CONTAINER_BUILD_DOCKERFILE $CERC_CONTAINER_BUILD_WORK_DIR

if [ $? -eq 0 ] && [ "$CERC_CONTAINER_BUILD_TAG" != "cerc/nextjs-base:local" ]; then
  cat <<EOF

#################################################################

Built host container for $CERC_CONTAINER_BUILD_WORK_DIR with tag:

    $CERC_CONTAINER_BUILD_TAG

To test locally run:

    docker run -p 3000:3000 --env-file /path/to/environment.env $CERC_CONTAINER_BUILD_TAG

EOF
fi
