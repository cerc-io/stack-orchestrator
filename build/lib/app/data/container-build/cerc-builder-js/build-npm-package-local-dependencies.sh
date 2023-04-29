#!/bin/bash
# Usage: build-npm-package-local-dependencies.sh <registry-url> <publish-with-this-version>
# Runs build-npm-package.sh after first fixing up yarn.lock to use a local
# npm registry for all packages in a specific scope (currently @cerc-io, @lirewine and @muknsys)
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
# Exit on error
set -e
local_npm_registry_url=$1
package_publish_version=$2
# If we need to handle an additional scope, add it to the list below:
npm_scopes_to_handle=("@cerc-io" "@lirewine" "@muknsys")
for npm_scope_for_local in ${npm_scopes_to_handle[@]}
do
    # We need to configure the local registry
    npm config set ${npm_scope_for_local}:registry ${local_npm_registry_url}
    npm config set -- ${local_npm_registry_url}:_authToken ${CERC_NPM_AUTH_TOKEN}
    # Find the set of dependencies from the specified scope
    mapfile -t dependencies_from_scope < <(cat package.json | jq -r '.dependencies | with_entries(if (.key|test("^'${npm_scope_for_local}'/.*$")) then ( {key: .key, value: .value } ) else empty end ) | keys[]')
    echo "Fixing up dependencies in scope ${npm_scope_for_local}"
    for package in "${dependencies_from_scope[@]}"
    do
        echo "Fixing up package ${package}"
        yarn-local-registry-fixup.sh $package ${local_npm_registry_url}
    done
done
echo "Running build"
build-npm-package.sh ${local_npm_registry_url} ${package_publish_version}
