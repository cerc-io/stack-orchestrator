#!/bin/bash

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

CERC_MIN_NEXTVER=13.4.2

CERC_NEXT_VERSION="${CERC_NEXT_VERSION:-keep}"
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

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
WORK_DIR="${1:-/app}"

cd "${WORK_DIR}" || exit 1

# If this file doesn't exist at all, we'll get errors below.
if [ ! -f "next.config.js" ]; then
  touch next.config.js
fi

if [ ! -f "next.config.dist" ]; then
  cp next.config.js next.config.dist
fi

which js-beautify >/dev/null
if [ $? -ne 0 ]; then
  npm i -g js-beautify
fi

js-beautify next.config.dist > next.config.js
echo "" >> next.config.js

WEBPACK_REQ_LINE=$(grep -n "require([\'\"]webpack[\'\"])" next.config.js | cut -d':' -f1)
if [ -z "$WEBPACK_REQ_LINE" ]; then
  cat > next.config.js.0 <<EOF
    const webpack = require('webpack');
EOF
fi

cat > next.config.js.1 <<EOF
let envMap;
try {
  // .env-list.json provides us a list of identifiers which should be replaced at runtime.
  envMap = require('./.env-list.json').reduce((a, v) => {
    a[v] = \`"CERC_RUNTIME_ENV_\${v.split(/\./).pop()}"\`;
    return a;
  }, {});
} catch {
  // If .env-list.json cannot be loaded, we are probably running in dev mode, so use process.env instead.
  envMap = Object.keys(process.env).reduce((a, v) => {
    if (v.startsWith('CERC_')) {
      a[\`process.env.\${v}\`] = JSON.stringify(process.env[v]);
    }
    return a;
  }, {});
}
EOF

CONFIG_LINES=$(wc -l next.config.js | awk '{ print $1 }')
ENV_LINE=$(grep -n 'env:' next.config.js | cut -d':' -f1)
WEBPACK_CONF_LINE=$(egrep -n 'webpack:\s+\([^,]+,' next.config.js | cut -d':' -f1)
NEXT_SECTION_ADJUSTMENT=0

if [ -n "$WEBPACK_CONF_LINE" ]; then
  WEBPACK_CONF_VAR=$(egrep -n 'webpack:\s+\([^,]+,' next.config.js | cut -d',' -f1 | cut -d'(' -f2)
  head -$(( ${WEBPACK_CONF_LINE} )) next.config.js > next.config.js.2
  cat > next.config.js.3 <<EOF
      $WEBPACK_CONF_VAR.plugins.push(new webpack.DefinePlugin(envMap));
EOF
  NEXT_SECTION_LINE=$((WEBPACK_CONF_LINE))
elif [ -n "$ENV_LINE" ]; then
  head -$(( ${ENV_LINE} - 1 )) next.config.js > next.config.js.2
  cat > next.config.js.3 <<EOF
    webpack: (config) => {
      config.plugins.push(new webpack.DefinePlugin(envMap));
      return config;
    },
EOF
  NEXT_SECTION_ADJUSTMENT=1
  NEXT_SECTION_LINE=$ENV_LINE
else
  echo "WARNING: Cannot find location to insert environment variable map in next.config.js" 1>&2
  rm -f next.config.js.*
  NEXT_SECTION_LINE=0
fi

tail -$(( ${CONFIG_LINES} - ${NEXT_SECTION_LINE} + ${NEXT_SECTION_ADJUSTMENT} )) next.config.js > next.config.js.5

cat next.config.js.* | sed 's/^ *//g' | js-beautify | grep -v 'process\.\env\.' | js-beautify > next.config.js
rm next.config.js.*

"${SCRIPT_DIR}/find-env.sh" "$(pwd)" > .env-list.json

if [ ! -f "package.dist" ]; then
  cp package.json package.dist
fi

cat package.dist | jq '.scripts.cerc_compile = "next experimental-compile"' | jq '.scripts.cerc_generate = "next experimental-generate"' > package.json

CUR_NEXT_VERSION="`jq -r '.dependencies.next' package.json`"

if [ "$CERC_NEXT_VERSION" != "keep" ] && [ "$CUR_NEXT_VERSION" != "$CERC_NEXT_VERSION" ]; then
  echo "Changing 'next' version specifier from '$CUR_NEXT_VERSION' to '$CERC_NEXT_VERSION' (set with '--extra-build-args \"--build-arg CERC_NEXT_VERSION=$CERC_NEXT_VERSION\"')"
  cat package.json | jq ".dependencies.next = \"$CERC_NEXT_VERSION\"" > package.json.$$
  mv package.json.$$ package.json
fi

time $CERC_BUILD_TOOL install || exit 1

CUR_NEXT_VERSION=`jq -r '.version' node_modules/next/package.json`

semver -p -r ">=$CERC_MIN_NEXTVER" $CUR_NEXT_VERSION
if [ $? -ne 0 ]; then
  cat <<EOF

###############################################################################

WARNING: 'next' $CUR_NEXT_VERSION < minimum version $CERC_MIN_NEXTVER.

Attempting to build with '^$CERC_MIN_NEXTVER'.  If this fails, you should upgrade
the dependency in your webapp, or specify an explicit 'next' version
to use for the build with:

     --extra-build-args "--build-arg CERC_NEXT_VERSION=<version>"

###############################################################################

EOF
  cat package.json | jq ".dependencies.next = \"^$CERC_MIN_NEXTVER\"" > package.json.$$
  mv package.json.$$ package.json
  time $CERC_BUILD_TOOL install || exit 1
fi

time $CERC_BUILD_TOOL run cerc_compile || exit 1

exit 0
