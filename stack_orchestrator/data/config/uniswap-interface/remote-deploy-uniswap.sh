#!/bin/bash

# $1: Remote user host
# $2: Path to run the app installation in (where urbit ship dir is located)
# $3: Glob file URL (eg. https://xyz.com/glob-abcd.glob)

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <username@remote_host> </path/to/remote/folder> <glob_url>"
  exit 1
fi

remote_user_host="$1"
remote_folder="$2"
glob_url="$3"

installation_script="./install-uniswap-app.sh"

ssh "$remote_user_host" "cd $remote_folder && bash -s $glob_url" < "$installation_script"
