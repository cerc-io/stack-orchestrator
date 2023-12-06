#!/bin/bash

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

if [ -z "$CERC_URBIT_APP" ]; then
  echo "CERC_URBIT_APP not set, exiting"
  exit 0
fi

echo "Creating Urbit application for ${CERC_URBIT_APP}"

app_desk_dir=/urbit/zod/${CERC_URBIT_APP}
if [ -d ${app_desk_dir} ]; then
  echo "Desk dir already exists for ${CERC_URBIT_APP}, skipping deployment..."
  exit 0
fi

app_build=/app-builds/${CERC_URBIT_APP}/build
app_mark_files=/app-builds/${CERC_URBIT_APP}/mar
app_docket_file=/app-builds/${CERC_URBIT_APP}/desk.docket-0

echo "Reading app build from ${app_build}"
echo "Reading additional mark files from ${app_mark_files}"
echo "Reading docket file ${app_docket_file}"

# Loop until the app's build appears
while [ ! -d ${app_build} ]; do
  echo "${CERC_URBIT_APP} app build not found, retrying in 5s..."
  sleep 5
done
echo "Build found..."

echo "Using IPFS endpoint ${CERC_IPFS_GLOB_HOST_ENDPOINT} for hosting the ${CERC_URBIT_APP} glob"
echo "Using IPFS server endpoint ${CERC_IPFS_SERVER_ENDPOINT} for reading ${CERC_URBIT_APP} glob"
ipfs_host_endpoint=${CERC_IPFS_GLOB_HOST_ENDPOINT}
ipfs_server_endpoint=${CERC_IPFS_SERVER_ENDPOINT}

# Fire curl requests to perform operations on the ship
dojo () {
  curl -s --data '{"source":{"dojo":"'"$1"'"},"sink":{"stdout":null}}' http://localhost:12321
}

hood () {
  curl -s --data '{"source":{"dojo":"+hood/'"$1"'"},"sink":{"app":"hood"}}' http://localhost:12321
}

# Create / mount the app's desk
hood "merge %${CERC_URBIT_APP} our %landscape"
hood "mount %${CERC_URBIT_APP}"

# Copy over build to desk data dir
cp -r ${app_build} ${app_desk_dir}

# Copy over the additional mark files
cp ${app_mark_files}/* ${app_desk_dir}/mar/

rm "${app_desk_dir}/desk.bill"
rm "${app_desk_dir}/desk.ship"

# Commit changes and create a glob
hood "commit %${CERC_URBIT_APP}"
dojo "-landscape!make-glob %${CERC_URBIT_APP} /build"

glob_file=$(ls -1 -c zod/.urb/put | head -1)
echo "Created glob file: ${glob_file}"

upload_response=$(curl -X POST -F file=@./zod/.urb/put/${glob_file} ${ipfs_host_endpoint}/api/v0/add)
glob_cid=$(echo "$upload_response" | grep -o '"Hash":"[^"]*' | sed 's/"Hash":"//')

echo "Glob file uploaded to IFPS:"
echo "{ cid: ${glob_cid}, filename: ${glob_file} }"

# Curl and wait for the glob to be hosted
glob_url="${ipfs_server_endpoint}/ipfs/${glob_cid}?filename=${glob_file}"

echo "Checking if glob file hosted at ${glob_url}"
while true; do
  response=$(curl -sL -w "%{http_code}" -o /dev/null "$glob_url")

  if [ $response -eq 200 ]; then
    echo "File found at $glob_url"
    break  # Exit the loop if the file is found
  else
    echo "File not found, retrying in a 5s..."
    sleep 5
  fi
done

glob_hash=$(echo "$glob_file" | sed "s/glob-\([a-z0-9\.]*\).glob/\1/")

# Replace the docket file for app
# Substitue the glob URL and hash
cp ${app_docket_file} ${app_desk_dir}/
sed -i "s|REPLACE_WITH_GLOB_URL|${glob_url}|g; s|REPLACE_WITH_GLOB_HASH|${glob_hash}|g" ${app_desk_dir}/desk.docket-0

# Commit changes and install the app
hood "commit %uniswap"
hood "install our %uniswap"

echo "Uniswap app installed"
