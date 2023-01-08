#!/bin/bash
# Usage: yarn-local-registry-fixup.sh <package-to-fix> <registry-url>
# Assumes package.json and yarn.lock are in the cwd
# The purpose of this script is to take a project cloned from git
# and "fixup" its yarn.lock file such that specified dependency
# will be fetched from a registry other than the one used when
# yarn.lock was generated. It updates all checksums using data
# from the "new" registry (because due to embedded timestamps etc
# the same source code re-built later will not have the same checksum).
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi
if [[ $# -ne 2 ]]; then
    echo "Illegal number of parameters" >&2
    exit 1
fi
target_package=$1
local_npm_registry_url=$2
# TODO: use jq rather than sed here:
versioned_target_package=$(grep ${target_package} package.json | sed -e 's#[[:space:]]\{1,\}\"\('${target_package}'\)\":[[:space:]]\{1,\}\"\(.*\)\",#\1@\2#' )
# Use yarn info to get URL checksums etc from the new registry
yarn_info_output=$(yarn info --json $versioned_target_package 2>/dev/null)
# Code below parses out the values we need
package_tarball=$(echo $yarn_info_output | jq -r .data.dist.tarball)
# When running inside a container, the registry can return a URL with the wrong host name due to proxying
# so we need to check if that has happened and fix the URL if so.
if ! [[ "${package_tarball}" =~ ^${local_npm_registry_url}.* ]]; then
    # HACK: I've hard-wired the host names below. Replace with proper implementation
    # TODO: remove the hack when proven no longer necessary
    package_tarball=$( echo ${package_tarball} | sed -e 's/localhost/gitea.local/g' )
fi
package_integrity=$(echo $yarn_info_output | jq -r .data.dist.integrity)
package_shasum=$(echo $yarn_info_output | jq -r .data.dist.shasum)
package_resolved=${package_tarball}#${package_shasum}
# Some strings need to be escaped so they work when passed to sed later
escaped_package_resolved=$(printf '%s\n' "$package_resolved" | sed -e 's/[\/&]/\\&/g')
escaped_target_package=$(printf '%s\n' "$target_package" | sed -e 's/[\/&]/\\&/g')
if [ -n "$CERC_SCRIPT_VERBOSE" ]; then
    echo "Tarball: ${package_tarball}"
    echo "Integrity: ${package_integrity}"
    echo "Shasum: ${package_shasum}"
    echo "Resolved: ${package_resolved}"
fi
# Use magic sed regex to replace the values in yarn.lock
# Note: yarn.lock is not json so we can not use jq for this
sed -i -e '/^\"'${escaped_target_package}'.*\":$/ , /^\".*$/ s/^\([[:space:]]\{1,\}resolved \).*$/\1'\"${escaped_package_resolved}\"'/' yarn.lock
sed -i -e '/^\"'${escaped_target_package}'.*\":$/ , /^\".*$/ s/^\([[:space:]]\{1,\}integrity \).*$/\1'${package_integrity}'/' yarn.lock
