#!/usr/bin/env bash
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

CERC_WEBAPP_FILES_DIR="${CERC_WEBAPP_FILES_DIR:-/app}"
cd "$CERC_WEBAPP_FILES_DIR"

rm -rf .next-r
"$SCRIPT_DIR/apply-runtime-env.sh" "`pwd`" .next .next-r
npm start .next-r -p ${CERC_LISTEN_PORT:-3000}
