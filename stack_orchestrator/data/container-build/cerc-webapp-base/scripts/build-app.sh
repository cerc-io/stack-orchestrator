#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

CERC_BUILD_TOOL="${CERC_BUILD_TOOL}"
WORK_DIR="${1:-/app}"
OUTPUT_DIR="${2:-build}"
DEST_DIR="${3:-/data}"

if [ -f "${WORK_DIR}/build-webapp.sh" ]; then
  echo "Building webapp with ${WORK_DIR}/build-webapp.sh ..."
  cd "${WORK_DIR}" || exit 1

  rm -rf "${DEST_DIR}"
  ./build-webapp.sh "${DEST_DIR}" || exit 1
elif [ -f "${WORK_DIR}/package.json" ]; then
  echo "Building node-based webapp ..."
  cd "${WORK_DIR}" || exit 1

  if [ -z "$CERC_BUILD_TOOL" ]; then
    if [ -f "yarn.lock" ]; then
      CERC_BUILD_TOOL=yarn
    else
      CERC_BUILD_TOOL=npm
    fi
  fi

  $CERC_BUILD_TOOL install || exit 1
  $CERC_BUILD_TOOL build || exit 1

  rm -rf "${DEST_DIR}"
  mv "${WORK_DIR}/${OUTPUT_DIR}" "${DEST_DIR}"
else
  echo "Copying static app ..."
  mv "${WORK_DIR}" "${DEST_DIR}"
fi

# One special fix ...
cd "${DEST_DIR}"
for f in $(find . -type f -name '*.htm*'); do
  sed -i -e 's#/LACONIC_HOSTED_CONFIG_homepage/#LACONIC_HOSTED_CONFIG_homepage/#g' "$f"
done

exit 0
