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
# Exit on error
set -e
# Get the name of this package from package.json since we weren't passed that
package_name=$( cat package.json | jq -r .name )
local_npm_registry_url=$1
npm config set @cerc-io:registry ${local_npm_registry_url}
npm config set @lirewine:registry ${local_npm_registry_url}
# Workaround bug in npm unpublish where it needs the url to be of the form //<foo> and not http://<foo>
local_npm_registry_url_fixed=$( echo ${local_npm_registry_url} | sed -e 's/^http[s]\{0,1\}://')
npm config set -- ${local_npm_registry_url_fixed}:_authToken ${CERC_NPM_AUTH_TOKEN}
# First check if the version of this package we're trying to build already exists in the registry
package_exists=$( yarn info --json ${package_name}@${package_publish_version} 2>/dev/null | jq -r .data.dist.tarball )
if [[ ! -z "$package_exists" && "$package_exists" != "null" ]]; then
    echo "${package_publish_version} of ${package_name} already exists in the registry
    if [[ ${CERC_FORCE_REBUILD} == "true" ]]; then
        # Attempt to unpublish the existing package
        echo "unpublishing existing package version since force rebuild is enabled"
        npm unpublish ${package_name}@${package_publish_version}
    else
        echo "skipping build since target version already exists"
        exit 0
    fi
fi
echo "Build and publish ${package_name} version ${package_publish_version}"
yarn install
yarn build
yarn publish --non-interactive  --new-version ${package_publish_version} --no-git-tag-version
