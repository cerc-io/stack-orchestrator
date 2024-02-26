#!/usr/bin/env bash
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi


SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CERC_MAX_GENERATE_TIME=${CERC_MAX_GENERATE_TIME:-60}
tpid=""

ctrl_c() {
    kill $tpid $(ps -ef | grep node | grep next | awk '{print $2}') 2>/dev/null
}

trap ctrl_c INT

CERC_BUILD_TOOL="${CERC_BUILD_TOOL}"
if [ -z "$CERC_BUILD_TOOL" ]; then
  if [ -f "pnpm-lock.yaml" ]; then
    CERC_BUILD_TOOL=pnpm
  elif [ -f "yarn.lock" ]; then
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
    tail -f gen.out &
    tpid=$!

    count=0
    generate_done="false"
    while [ $count -lt $CERC_MAX_GENERATE_TIME ] && [ "$generate_done" == "false" ]; do
      sleep 1
      count=$((count + 1))
      grep 'rendered as static' gen.out > /dev/null
      if [ $? -eq 0 ]; then
        generate_done="true"
      fi
    done

    if [ $generate_done != "true" ]; then
      echo "ERROR: 'npm run cerc_generate' not successful within CERC_MAX_GENERATE_TIME" 1>&2
      exit 1
    fi

    kill $tpid $(ps -ef | grep node | grep next | grep generate | awk '{print $2}') 2>/dev/null
    tpid=""
  fi
fi

$CERC_BUILD_TOOL start . -- -p ${CERC_LISTEN_PORT:-80}
