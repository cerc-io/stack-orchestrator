#!/bin/bash

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

CERC_MIN_NEXTVER=13.4.2
CERC_DEFAULT_WEBPACK_VER="5.93.0"

CERC_NEXT_VERSION="${CERC_NEXT_VERSION:-keep}"
CERC_WEBPACK_VERSION="${CERC_WEBPACK_VERSION:-keep}"

CERC_BUILD_TOOL="${CERC_BUILD_TOOL}"
if [ -z "$CERC_BUILD_TOOL" ]; then
  if [ -f "pnpm-lock.yaml" ]; then
    CERC_BUILD_TOOL=pnpm
  elif [ -f "yarn.lock" ]; then
    CERC_BUILD_TOOL=yarn
  elif [ -f "bun.lockb" ]; then
    CERC_BUILD_TOOL=bun
  else
    CERC_BUILD_TOOL=npm
  fi
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
WORK_DIR="${1:-/app}"

cd "${WORK_DIR}" || exit 1

if [ -f "next.config.mjs" ]; then
  NEXT_CONFIG_JS="next.config.mjs"
  IMPORT_OR_REQUIRE="import"
else
  NEXT_CONFIG_JS="next.config.js"
  IMPORT_OR_REQUIRE="require"
fi

# If this file doesn't exist at all, we'll get errors below.
if [ ! -f "${NEXT_CONFIG_JS}" ]; then
  touch ${NEXT_CONFIG_JS}
fi

if [ ! -f "next.config.dist" ]; then
  cp $NEXT_CONFIG_JS next.config.dist
fi

which js-beautify >/dev/null
if [ $? -ne 0 ]; then
  npm i -g js-beautify
fi

# js-beautify formats NEXTJS_CONFIG_FILE (ie next.config.js / next.config.mjs) so we can reliably transformable later
js-beautify next.config.dist > ${NEXT_CONFIG_JS}
echo "" >> ${NEXT_CONFIG_JS}

if [ "${IMPORT_OR_REQUIRE}" == "require" ]; then
  WEBPACK_REQ_LINE=$(grep -n "require([\'\"]webpack[\'\"])" ${NEXT_CONFIG_JS} | cut -d':' -f1)
  if [ -z "$WEBPACK_REQ_LINE" ]; then
    cat > ${NEXT_CONFIG_JS}.0 <<EOF
    const webpack = require('webpack');
EOF
  fi
else
  WEBPACK_IMPORT_LINE=$(grep -n "^import .*[\'\"]webpack[\'\"];?$" ${NEXT_CONFIG_JS} | cut -d':' -f1)
  if [ -z "$WEBPACK_IMPORT_LINE" ]; then
    cat > ${NEXT_CONFIG_JS}.0 <<EOF
    import webpack from 'webpack';
EOF
  fi
  CREATE_REQUIRE_LINE=$(grep -n "require = createRequire" ${NEXT_CONFIG_JS} | cut -d':' -f1)
  if [ -z "$CREATE_REQUIRE_LINE" ]; then
    cat >> ${NEXT_CONFIG_JS}.0 <<EOF
    import { createRequire } from "module";
    const require = createRequire(import.meta.url);
EOF
  fi
fi

cat > ${NEXT_CONFIG_JS}.1 <<EOF
let envMap;
try {
  // .env-list.json provides us a list of identifiers which should be replaced at runtime.
  envMap = require('./.env-list.json').reduce((a, v) => {
    a[v] = \`"CERC_RUNTIME_ENV_\${v.split(/\./).pop()}"\`;
    return a;
  }, {});
} catch (e) {
  console.error(e);
  // If .env-list.json cannot be loaded, we are probably running in dev mode, so use process.env instead.
  envMap = Object.keys(process.env).reduce((a, v) => {
    if (v.startsWith('CERC_')) {
      a[\`process.env.\${v}\`] = JSON.stringify(process.env[v]);
    }
    return a;
  }, {});
}
console.log(envMap);
EOF

CONFIG_LINES=$(wc -l ${NEXT_CONFIG_JS} | awk '{ print $1 }')
ENV_LINE=$(grep -n 'env:' ${NEXT_CONFIG_JS} | cut -d':' -f1)
WEBPACK_CONF_LINE=$(egrep -n 'webpack:\s+\([^,]+,' ${NEXT_CONFIG_JS} | cut -d':' -f1)
NEXT_SECTION_ADJUSTMENT=0

if [ -n "$WEBPACK_CONF_LINE" ]; then
  WEBPACK_CONF_VAR=$(egrep -n 'webpack:\s+\([^,]+,' ${NEXT_CONFIG_JS} | cut -d',' -f1 | cut -d'(' -f2)
  head -$(( ${WEBPACK_CONF_LINE} )) ${NEXT_CONFIG_JS} > ${NEXT_CONFIG_JS}.2
  cat > ${NEXT_CONFIG_JS}.3 <<EOF
      $WEBPACK_CONF_VAR.plugins.push(new webpack.DefinePlugin(envMap));
EOF
  NEXT_SECTION_LINE=$((WEBPACK_CONF_LINE))
elif [ -n "$ENV_LINE" ]; then
  head -$(( ${ENV_LINE} - 1 )) ${NEXT_CONFIG_JS} > ${NEXT_CONFIG_JS}.2
  cat > ${NEXT_CONFIG_JS}.3 <<EOF
    webpack: (config) => {
      config.plugins.push(new webpack.DefinePlugin(envMap));
      return config;
    },
EOF
  NEXT_SECTION_ADJUSTMENT=1
  NEXT_SECTION_LINE=$ENV_LINE
else
  echo "WARNING: Cannot find location to insert environment variable map in ${NEXT_CONFIG_JS}" 1>&2
  rm -f ${NEXT_CONFIG_JS}.*
  NEXT_SECTION_LINE=0
fi

tail -$(( ${CONFIG_LINES} - ${NEXT_SECTION_LINE} + ${NEXT_SECTION_ADJUSTMENT} )) ${NEXT_CONFIG_JS} > ${NEXT_CONFIG_JS}.4

rm -f ${NEXT_CONFIG_JS}
for ((i=0; i <=5; i++)); do
  if [ -f "${NEXT_CONFIG_JS}.${i}" ]; then
    if [ $i -le 2 ] ; then
      cat ${NEXT_CONFIG_JS}.${i} >> ${NEXT_CONFIG_JS}
    else
      cat ${NEXT_CONFIG_JS}.${i} | sed 's/^ *//g' | js-beautify | grep -v 'process\.\env\.' | js-beautify >> ${NEXT_CONFIG_JS}
    fi
  fi
done
rm ${NEXT_CONFIG_JS}.*

"${SCRIPT_DIR}/find-env.sh" "$(pwd)" > .env-list.json

if [ ! -f "package.dist" ]; then
  cp package.json package.dist
fi

CUR_NEXT_VERSION="`jq -r '.dependencies.next' package.json`"

if [ "$CERC_NEXT_VERSION" != "keep" ] && [ "$CUR_NEXT_VERSION" != "$CERC_NEXT_VERSION" ]; then
  echo "Changing 'next' version specifier from '$CUR_NEXT_VERSION' to '$CERC_NEXT_VERSION' (set with '--extra-build-args \"--build-arg CERC_NEXT_VERSION=$CERC_NEXT_VERSION\"')"
  cat package.json | jq ".dependencies.next = \"$CERC_NEXT_VERSION\"" > package.json.$$
  mv package.json.$$ package.json
fi

CUR_WEBPACK_VERSION="`jq -r '.dependencies.webpack' package.json`"
if [ -z "$CUR_WEBPACK_VERSION" ]; then
  CUR_WEBPACK_VERSION="`jq -r '.devDependencies.webpack' package.json`"
fi
if [ "${CERC_WEBPACK_VERSION}" != "keep" ] || [ "${CUR_WEBPACK_VERSION}" == "null" ]; then
  if [ -z "$CERC_WEBPACK_VERSION" ] || [ "$CERC_WEBPACK_VERSION" == "keep" ]; then
    CERC_WEBPACK_VERSION="${CERC_DEFAULT_WEBPACK_VER}"
  fi
  echo "Webpack is required for env variable substitution.  Adding to webpack@$CERC_WEBPACK_VERSION to dependencies..." 1>&2
  cat package.json | jq ".dependencies.webpack = \"$CERC_WEBPACK_VERSION\"" > package.json.$$
  mv package.json.$$ package.json
fi

time $CERC_BUILD_TOOL install || exit 1

CUR_NEXT_VERSION=`jq -r '.version' node_modules/next/package.json`

# See https://github.com/vercel/next.js/discussions/46544
semver -p -r ">=14.2.0" "$CUR_NEXT_VERSION"
if [ $? -eq 0 ]; then
  # For >= 14.2.0
  CERC_NEXT_COMPILE_COMMAND="next build --experimental-build-mode compile"
  CERC_NEXT_GENERATE_COMMAND="next build --experimental-build-mode generate"
else
  # For 13.4.2 to 14.1.x
  CERC_NEXT_COMPILE_COMMAND="next experimental-compile"
  CERC_NEXT_GENERATE_COMMAND="next experimental-generate"
fi

cat package.json | jq ".scripts.cerc_compile = \"$CERC_NEXT_COMPILE_COMMAND\"" | jq ".scripts.cerc_generate = \"$CERC_NEXT_GENERATE_COMMAND\"" > package.json.$$
mv package.json.$$ package.json

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
