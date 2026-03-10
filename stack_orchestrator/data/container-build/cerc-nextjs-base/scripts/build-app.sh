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

if [ -f "${WORK_DIR}/build-webapp.sh" ]; then
  echo "Building webapp with ${WORK_DIR}/build-webapp.sh ..."
cd "${WORK_DIR}" || exit 1

  ./build-webapp.sh || exit 1
  exit 0
fi

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

grep 'withPWA' ${NEXT_CONFIG_JS} >/dev/null && HAS_WITHPWA=true || HAS_WITHPWA=false

if [ "$HAS_WITHPWA" == "true" ]; then
  if [ "$IMPORT_OR_REQUIRE" == "import" ]; then
    cat > ${NEXT_CONFIG_JS}.2 <<EOF
const __xPWA__ = (p) => {
  const realPWA = withPWA(p);
  return (nextConfig) => {
    const modConfig = {...nextConfig};

    modConfig.webpack = (config) => {
      config.plugins.push(new webpack.DefinePlugin(envMap));
      return nextConfig.webpack ? nextConfig.webpack(config) : config;
    };

    return realPWA(modConfig);
  };
};
EOF
  else
    cat > ${NEXT_CONFIG_JS}.3 <<EOF
const __xPWA__ = (nextConfig) => {
  const modConfig = {...nextConfig};

  modConfig.webpack = (config) => {
    config.plugins.push(new webpack.DefinePlugin(envMap));
    return nextConfig.webpack ? nextConfig.webpack(config) : config;
  };

  return withPWA(modConfig);
};
EOF
  fi

  cat ${NEXT_CONFIG_JS} | js-beautify | sed 's/withPWA(/__xPWA__(/g' > ${NEXT_CONFIG_JS}.4
else
    cat > ${NEXT_CONFIG_JS}.3 <<EOF
  const __xCfg__ = (nextConfig) => {
    const modConfig = {...nextConfig};

    modConfig.webpack = (config) => {
      config.plugins.push(new webpack.DefinePlugin(envMap));
      return nextConfig.webpack ? nextConfig.webpack(config) : config;
    };

    return modConfig;
  };
EOF
  if [ "$IMPORT_OR_REQUIRE" == "import" ]; then
    cat ${NEXT_CONFIG_JS} | js-beautify | sed 's/export\s\+default\s\+/const __orig_cfg__ = /g' > ${NEXT_CONFIG_JS}.4
    echo "export default __xCfg__(__orig_cfg__);" > ${NEXT_CONFIG_JS}.5
  else
    cat ${NEXT_CONFIG_JS} | js-beautify | sed 's/module.exports\s\+=\s\+/const __orig_cfg__ = /g' > ${NEXT_CONFIG_JS}.4
    echo "module.exports = __xCfg__(__orig_cfg__);" > ${NEXT_CONFIG_JS}.5
  fi
fi


rm -f ${NEXT_CONFIG_JS}
for ((i=0; i <= 10; i++)); do
  if [ -s "${NEXT_CONFIG_JS}.${i}" ]; then
    if [ $i -le 2 ] ; then
      cat ${NEXT_CONFIG_JS}.${i} >> ${NEXT_CONFIG_JS}
    else
      cat ${NEXT_CONFIG_JS}.${i} | sed 's/^ *//g' | js-beautify | grep -v 'process\.\env\.' | js-beautify >> ${NEXT_CONFIG_JS}
    fi
  fi
done
rm ${NEXT_CONFIG_JS}.*
cat ${NEXT_CONFIG_JS} | js-beautify > ${NEXT_CONFIG_JS}.pretty
mv ${NEXT_CONFIG_JS}.pretty ${NEXT_CONFIG_JS}

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
