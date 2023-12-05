#!/bin/bash

# $1: Remote user host
# $2: Remote Urbit ship's pier dir path (eg. /home/user/zod)
# $3: Glob file URL (eg. https://xyz.com/glob-0vabcd.glob)
# $4: Glob file hash (eg. 0vabcd)

if [ "$#" -ne 4 ]; then
  echo "Incorrect number of arguments"
  echo "Usage: $0 <username@remote_host> </path/to/remote/pier/folder> <glob_url> <glob_hash>"
  exit 1
fi

remote_user_host="$1"
remote_pier_folder="$2"
glob_url="$3"
glob_hash="$4"

installation_script="./install-uniswap-app.sh"

ssh "$remote_user_host" "bash -s $glob_url $glob_hash $remote_pier_folder" < "$installation_script"
