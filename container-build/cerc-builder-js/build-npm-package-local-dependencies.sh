#!/bin/bash
# Usage: build-npm-package-local-dependencies.sh <registry-url> <publish-with-this-version>
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi
if [[ $# -ne 2 ]]; then
    echo "Illegal number of parameters" >&2
    exit 1
fi
if [[ -z "${NPM_AUTH_TOKEN}" ]]; then
    echo "NPM_AUTH_TOKEN is not set" >&2
    exit 1
fi
local_npm_registry_url=$1
package_publish_version=$2
# TODO: make this a paramater and allow a list of scopes
npm_scope_for_local="@cerc-io"
# We need to configure the local registry 
npm config set @cerc-io:registry ${local_npm_registry_url}
npm config set -- ${local_npm_registry_url}:_authToken ${NPM_AUTH_TOKEN}
# Find the set of dependencies from the specified scope
mapfile -t dependencies_from_scope < <(cat package.json | jq -r '.dependencies | with_entries(if (.key|test("^@cerc-io/.*$")) then ( {key: .key, value: .value } ) else empty end ) | keys[]')
echo "Fixing up dependencies"
for package in "${dependencies_from_scope[@]}"
do
    yarn-local-registry-fixup.sh $package
done
echo "Running build"
build-npm-package.sh ${local_npm_registry_url} ${package_publish_version}
