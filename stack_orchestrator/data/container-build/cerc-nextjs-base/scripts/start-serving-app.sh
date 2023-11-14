#!/usr/bin/env bash
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi


SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CERC_MAX_GENERATE_TIME=${CERC_MAX_GENERATE_TIME:-60}

CERC_BUILD_TOOL="${CERC_BUILD_TOOL}"
if [ -z "$CERC_BUILD_TOOL" ]; then
  if [ -f "yarn.lock" ] && [ ! -f "package-lock.json" ]; then
    CERC_BUILD_TOOL=yarn
  else
    CERC_BUILD_TOOL=npm
  fi
fi

CERC_WEBAPP_FILES_DIR="${CERC_WEBAPP_FILES_DIR:-/app}"
cd "$CERC_WEBAPP_FILES_DIR"

"$SCRIPT_DIR/apply-runtime-env.sh" "`pwd`" .next .next-r
mv .next .next.old
mv .next-r/.next .

if [ "$CERC_NEXTJS_SKIP_GENERATE" != "true" ]; then
  jq -e '.scripts.cerc_generate' package.json >/dev/null
  if [ $? -eq 0 ]; then
    npm run cerc_generate > gen.out 2>&1 &
    timeout $CERC_MAX_GENERATE_TIME bash -c "tail -n0 -f gen.out | sed '/rendered as static HTML/ q'"
    if [ $? -ne 0 ]; then
      echo "ERROR: 'npm run cerc_generate' exceeded CERC_MAX_GENERATE_TIME."
      exit 1
    fi

    count=0
    while [ $count -lt 10 ]; do
      sleep 1
      ps -ef | grep 'node' | grep 'next' | grep 'generate' >/dev/null
      if [ $? -ne 0 ]; then 
        break
      else
        count=$((count + 1))
      fi
    done
    kill $(ps -ef |grep node | grep next | grep generate | awk '{print $2}') 2>/dev/null
  fi
fi

$CERC_BUILD_TOOL start . -p ${CERC_LISTEN_PORT:-3000}
