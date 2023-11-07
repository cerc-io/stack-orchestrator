#!/bin/bash

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

WORK_DIR="${1:-/app}"

cd "${WORK_DIR}" || exit 1

cp next.config.js next.config.dist

npm i -g js-beautify
js-beautify next.config.dist > next.config.js

npm install

CONFIG_LINES=$(wc -l next.config.js | awk '{ print $1 }')
MOD_EXPORTS_LINE=$(grep -n 'module.exports' next.config.js | cut -d':' -f1)

head -$(( ${MOD_EXPORTS_LINE} - 1 )) next.config.js > next.config.js.1

cat > next.config.js.2 <<EOF
const webpack = require('webpack');

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

grep 'module.exports' next.config.js > next.config.js.3

cat > next.config.js.4 <<EOF
  webpack: (config) => {
    config.plugins.push(new webpack.DefinePlugin(envMap));
    return config;
  },
EOF

tail -$(( ${CONFIG_LINES} - ${MOD_EXPORTS_LINE} + 1 )) next.config.js | grep -v 'process\.env\.' > next.config.js.5

cat next.config.js.* | js-beautify > next.config.js
rm next.config.js.*

"${SCRIPT_DIR}/find-env.sh" "$(pwd)" > .env-list.json

npm run build
rm .env-list.json