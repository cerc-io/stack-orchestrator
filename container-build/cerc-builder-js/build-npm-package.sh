#!/bin/bash
# Usage: build-npm-package.sh <registry-url> <publish-with-this-version>
# Note: supply the registry auth token in CERC_NPM_AUTH_TOKEN
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi
if ! [[ $# -eq 1 || $# -eq 2 ]]; then
    echo "Illegal number of parameters" >&2
    exit 1
fi
if [[ -z "${CERC_NPM_AUTH_TOKEN}" ]]; then
    echo "CERC_NPM_AUTH_TOKEN is not set" >&2
    exit 1
fi
if [[ $# -eq 2 ]]; then
    package_publish_version=$2
else
    package_publish_version=$( cat package.json | jq -r .version )
fi
local_npm_registry_url=$1
npm config set @lirewine:registry ${local_npm_registry_url}
npm config set @cerc-io:registry ${local_npm_registry_url}
npm config set -- ${local_npm_registry_url}:_authToken ${CERC_NPM_AUTH_TOKEN}
echo "Build and publish version ${package_publish_version}"
yarn install
yarn build
yarn publish --non-interactive  --new-version ${package_publish_version} --no-git-tag-version
