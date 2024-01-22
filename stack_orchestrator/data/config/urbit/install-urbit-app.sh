#!/bin/bash

# $1: App name (eg. uniswap)
# $2: Assets dir path (local) for app (eg. /home/user/myapp/urbit-files)
# $3: Glob file URL (eg. https://xyz.com/glob-0vabcd.glob)
# $4: Glob file hash (eg. 0vabcd)
# $5: Urbit ship's pier dir (default: ./zod)

if [ "$#" -lt 4 ]; then
  echo "Insufficient arguments"
  echo "Usage: $0 <app_name> </path/to/app/assets/folder> <glob_url> <glob_hash> [/path/to/remote/pier/folder]"
  exit 1
fi

app_name=$1
app_mark_files=$2/mar
app_docket_file=$2/desk.docket-0
echo "Creating Urbit application for ${app_name}"
echo "Reading additional mark files from ${app_mark_files}"
echo "Reading docket file ${app_docket_file}"

glob_url=$3
glob_hash=$4
echo "Using glob file from ${glob_url} with hash ${glob_hash}"

# Default pier dir: ./zod
# Default desk dir: ./zod/<app_name>
pier_dir="${5:-./zod}"
app_desk_dir="${pier_dir}/${app_name}"
echo "Using ${app_desk_dir} as the ${app_name} desk dir path"

# Fire curl requests to perform operations on the ship
dojo () {
  curl -s --data '{"source":{"dojo":"'"$1"'"},"sink":{"stdout":null}}' http://localhost:12321
}

hood () {
  curl -s --data '{"source":{"dojo":"+hood/'"$1"'"},"sink":{"app":"hood"}}' http://localhost:12321
}

# Create / mount the app's desk
hood "merge %${app_name} our %landscape"
hood "mount %${app_name}"

# Copy over the additional mark files
cp ${app_mark_files}/* ${app_desk_dir}/mar/

rm "${app_desk_dir}/desk.bill"
rm "${app_desk_dir}/desk.ship"

# Replace the docket file for app
# Substitue the glob URL and hash
cp ${app_docket_file} ${app_desk_dir}/
sed -i "s|REPLACE_WITH_GLOB_URL|${glob_url}|g; s|REPLACE_WITH_GLOB_HASH|${glob_hash}|g" ${app_desk_dir}/desk.docket-0

# Commit changes and install the app
hood "commit %${app_name}"
hood "install our %${app_name}"

echo "${app_name} app installed"
