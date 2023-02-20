#!/usr/bin/env bash
# Usage: default-build.sh <image-tag> [<repo-relative-path>]
# if <repo-relative-path> is not supplied, the context is the directory where the Dockerfile lives
if [[ -n "$CERC_SCRIPT_DEBUG" ]]; then
    set -x
fi
if [[ $# -ne 2 ]]; then
    echo "Illegal number of parameters" >&2
    exit 1
fi
image_tag=$1
build_dir=$2
echo "Building ${image_tag} in ${build_dir}"
docker build -t ${image_tag} ${build_dir}
