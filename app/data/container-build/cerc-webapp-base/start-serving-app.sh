#!/usr/bin/env bash
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

CERC_WEBAPP_FILES_DIR="${CERC_WEBAPP_FILES_DIR:-/data}"

/scripts/apply-webapp-config.sh /config/config.yml ${CERC_WEBAPP_FILES_DIR}
http-server -p 80 ${CERC_WEBAPP_FILES_DIR}
