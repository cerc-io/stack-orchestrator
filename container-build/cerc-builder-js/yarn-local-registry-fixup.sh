#!/bin/bash
# Usage: yarn-local-registry-fixup.sh <package-to-fix>
# Assumes package.json and yarn.lock are in the cwd
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi
if [[ $# -ne 1 ]]; then
    echo "Illegal number of parameters" >&2
    exit 1
fi
target_package=$1
versioned_target_package=$(grep ${target_package} package.json | sed -e 's#[[:space:]]\{1,\}\"\('${target_package}'\)\":[[:space:]]\{1,\}\"\(.*\)\",#\1@\2#' )
yarn_info_output=$(yarn info --json $versioned_target_package 2>/dev/null)
package_tarball=$(echo $yarn_info_output | jq -r .data.dist.tarball)
package_integrity=$(echo $yarn_info_output | jq -r .data.dist.integrity)
package_shasum=$(echo $yarn_info_output | jq -r .data.dist.shasum)
package_resolved=${package_tarball}#${package_shasum}
escaped_package_resolved=$(printf '%s\n' "$package_resolved" | sed -e 's/[\/&]/\\&/g')
escaped_target_package=$(printf '%s\n' "$target_package" | sed -e 's/[\/&]/\\&/g')
if [ -n "$CERC_SCRIPT_VERBOSE" ]; then
    echo "Tarball: ${package_tarball}"
    echo "Integrity: ${package_integrity}"
    echo "Shasum: ${package_shasum}"
    echo "Resolved: ${package_resolved}"
fi
sed -i -e '/^\"'${escaped_target_package}'.*\":$/ , /^\".*$/ s/^\([[:space:]]\{1,\}resolved \).*$/\1'\"${escaped_package_resolved}\"'/' yarn.lock
sed -i -e '/^\"'${escaped_target_package}'.*\":$/ , /^\".*$/ s/^\([[:space:]]\{1,\}integrity \).*$/\1'${package_integrity}'/' yarn.lock
