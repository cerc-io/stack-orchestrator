#!/bin/bash
# Usage: build-npm-package.sh <registry-url> <publish-with-this-version>
# Note: supply the registry auth token in CERC_NPM_AUTH_TOKEN
if [[ -n "$CERC_SCRIPT_DEBUG" ]]; then
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
# Get the name of this package from package.json since we weren't passed that
package_name=$( cat package.json | jq -r .name )
local_npm_registry_url=$1
npm config set @lirewine:registry ${local_npm_registry_url}
npm config set @cerc-io:registry ${local_npm_registry_url}
npm config set -- ${local_npm_registry_url}:_authToken ${CERC_NPM_AUTH_TOKEN}
# First check if the version of this package we're trying to build already exists in the registry
package_exists=$( yarn info --json ${package_name}@${package_publish_version} | jq -r .data.dist.tarball )
if [[ -n "$package_exists" ]]; then
    echo "${package_publish_version} of ${package_name} already exists in the registry, skipping build"
    exit 0
fi
echo "Build and publish ${package_name} version ${package_publish_version}"
yarn install
yarn build
yarn publish --non-interactive  --new-version ${package_publish_version} --no-git-tag-version
