#!/bin/bash

# $1: Remote user host
# $2: App name (eg. uniswap)
# $3: Assets dir path (local) for app (eg. /home/user/myapp/urbit-files)
# $4: Remote Urbit ship's pier dir path (eg. /home/user/zod)
# $5: Glob file URL (eg. https://xyz.com/glob-0vabcd.glob)
# $6: Glob file hash (eg. 0vabcd)

if [ "$#" -ne 6 ]; then
  echo "Incorrect number of arguments"
  echo "Usage: $0 <username@remote_host> <app_name> </path/to/app/assets/folder> </path/to/remote/pier/folder> <glob_url> <glob_hash>"
  exit 1
fi

remote_user_host="$1"
app_name=$2
app_assets_folder=$3
remote_pier_folder="$4"
glob_url="$5"
glob_hash="$6"

installation_script="./install-urbit-app.sh"

# Copy over the assets to remote machine in a tmp dir
remote_app_assets_folder=/tmp/urbit-app-assets/$app_name
ssh "$remote_user_host" "mkdir -p $remote_app_assets_folder"
scp -r $app_assets_folder/* $remote_user_host:$remote_app_assets_folder

# Run the installation script
ssh "$remote_user_host" "bash -s $app_name $remote_app_assets_folder '${glob_url}' $glob_hash $remote_pier_folder" < "$installation_script"

# Remove the tmp assets dir
ssh "$remote_user_host" "rm -rf $remote_app_assets_folder"
