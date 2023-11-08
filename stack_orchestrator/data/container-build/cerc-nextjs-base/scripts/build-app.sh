#!/bin/bash

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

WORK_DIR="${1:-/app}"

cd "${WORK_DIR}" || exit 1

if [ ! -f "next.config.dist" ]; then
  cp next.config.js next.config.dist
fi

which js-beautify >/dev/null
if [ $? -ne 0 ]; then
  npm i -g js-beautify
fi

js-beautify next.config.dist > next.config.js

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
  NEXT_SECTION_LINE=$((WEBPACK_CONF_LINE - 1))
elif [ -n "$ENV_LINE" ]; then
  head -$(( ${ENV_LINE} - 1 )) next.config.js > next.config.js.2
  cat > next.config.js.3 <<EOF
    webpack: (config) => {
      config.plugins.push(new webpack.DefinePlugin(envMap));
      return config;
    },
EOF
  NEXT_SECTION_ADJUSTMENT=2
  NEXT_SECTION_LINE=$ENV_LINE
else
  echo "WARNING: Cannot find location to insert environment variable map in next.config.js" 1>&2
  rm -f next.config.js.*
  NEXT_SECTION_LINE=0
fi

tail -$(( ${CONFIG_LINES} - ${NEXT_SECTION_LINE} + ${NEXT_SECTION_ADJUSTMENT} )) next.config.js > next.config.js.5

cat next.config.js.* | sed 's/^ *//g' | js-beautify | grep -v 'process\.\env\.' | js-beautify | tee next.config.js
rm next.config.js.*

"${SCRIPT_DIR}/find-env.sh" "$(pwd)" > .env-list.json

npm install || exit 1
npm run build || exit 1

exit 0
