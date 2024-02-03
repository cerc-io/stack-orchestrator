#!/usr/bin/env bash
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

CERC_WEBAPP_FILES_DIR="${CERC_WEBAPP_FILES_DIR:-/data}"
CERC_ENABLE_CORS="${CERC_ENABLE_CORS:-false}"

if [ "true" == "$CERC_ENABLE_CORS" ]; then
  CERC_HTTP_EXTRA_ARGS="$CERC_HTTP_EXTRA_ARGS --cors"
fi

/scripts/apply-webapp-config.sh /config/config.yml ${CERC_WEBAPP_FILES_DIR}
/scripts/apply-runtime-env.sh ${CERC_WEBAPP_FILES_DIR}
http-server $CERC_HTTP_EXTRA_ARGS -p ${CERC_LISTEN_PORT:-80} ${CERC_WEBAPP_FILES_DIR}
