#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

# Check and exit if a deployment already exists (on restarts)
if [ -d /app-builds/vega/build ]; then
  echo "Build already exists, remove volume to rebuild"
  exit 0
fi

./docker/prepare-dist.sh

# Post-process the output: rename files, e.g., `AlphaLyrae.woff2` => `alphalyrae.woff2`
while read filepath; do
  filename=$(basename "$filepath")
  dir=$(dirname "$filepath")
  if echo "$filename" | grep -q "[A-Z]"; then
    newfilename=$(tr '[:upper:]' '[:lower:]' <<< "$filename")
    echo "Translating '$filepath' => $dir/$newfilename'"
    mv "$filepath" "$dir/$newfilename"
    find dist-result -type f | xargs sed -i "s/$filename/$newfilename/g"
  fi
done < <(find dist-result/ -type f)


# Copy over dist-result and other files to `app-builds` volume for urbit deployment
mkdir -p /app-builds/vega
cp -r ./dist-result /app-builds/vega/build
cp -r urbit-files/* /app-builds/vega/
