#!/bin/bash

# $1: Remote user host
# $2: Remote Urbit ship's pier dir path (eg. /home/user/zod)
# $3: Glob file URL (eg. https://xyz.com/glob-abcd.glob)

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <username@remote_host> </path/to/remote/pier/folder> <glob_url>"
  exit 1
fi

remote_user_host="$1"
remote_pier_folder="$2"
glob_url="$3"

installation_script="./install-uniswap-app.sh"

ssh "$remote_user_host" "bash -s $glob_url $remote_pier_folder" < "$installation_script"
