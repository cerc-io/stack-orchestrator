#!/usr/bin/env bash
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

CERC_LISTEN_PORT=${CERC_LISTEN_PORT:-80}
CERC_WEBAPP_FILES_DIR="${CERC_WEBAPP_FILES_DIR:-/data}"
CERC_ENABLE_CORS="${CERC_ENABLE_CORS:-false}"
CERC_SINGLE_PAGE_APP="${CERC_SINGLE_PAGE_APP}"

if [ -z "${CERC_SINGLE_PAGE_APP}" ]; then
  CERC_SINGLE_PAGE_APP=false
  if [ 1 -eq $(find "${CERC_WEBAPP_FILES_DIR}" -name '*.html' | wc -l) ]; then
    if [ -d "${CERC_WEBAPP_FILES_DIR}/static" ] || [ -d "${CERC_WEBAPP_FILES_DIR}/assets" ]; then
      CERC_SINGLE_PAGE_APP=true
    fi
  fi
fi

if [ "true" == "$CERC_ENABLE_CORS" ]; then
  CERC_HTTP_EXTRA_ARGS="$CERC_HTTP_EXTRA_ARGS --cors"
fi

if [ "true" == "$CERC_SINGLE_PAGE_APP" ]; then
  echo "Serving content as single-page app.  If this is wrong, set 'CERC_SINGLE_PAGE_APP=false'"
  # Create a catchall redirect back to /
  CERC_HTTP_EXTRA_ARGS="$CERC_HTTP_EXTRA_ARGS --proxy http://localhost:${CERC_LISTEN_PORT}?"
else
  echo "Serving content normally.  If this is a single-page app, set 'CERC_SINGLE_PAGE_APP=true'"
fi

LACONIC_HOSTED_CONFIG_FILE=${LACONIC_HOSTED_CONFIG_FILE}
if [ -z "${LACONIC_HOSTED_CONFIG_FILE}" ]; then
  if [ -f "/config/laconic-hosted-config.yml" ]; then
    LACONIC_HOSTED_CONFIG_FILE="/config/laconic-hosted-config.yml"
  elif [ -f "/config/config.yml" ]; then
    LACONIC_HOSTED_CONFIG_FILE="/config/config.yml"
  fi
fi

if [ -f "${LACONIC_HOSTED_CONFIG_FILE}" ]; then
  /scripts/apply-webapp-config.sh $LACONIC_HOSTED_CONFIG_FILE "${CERC_WEBAPP_FILES_DIR}"
fi

/scripts/apply-runtime-env.sh ${CERC_WEBAPP_FILES_DIR}
http-server $CERC_HTTP_EXTRA_ARGS -p ${CERC_LISTEN_PORT} "${CERC_WEBAPP_FILES_DIR}"
