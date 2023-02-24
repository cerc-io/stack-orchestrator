#!/bin/bash
# Make the container usable for uid/gid != 1000
if [[ -n "$CERC_SCRIPT_DEBUG" ]]; then
    set -x
fi
current_uid=$(id -u)
current_gid=$(id -g)
user_name="hostuser"
# First check the current uid. If == 1000 then exit, nothing needed because that uid already exists
if [[ ${current_uid} == 1000 ]]; then
    exit 0
fi
# Also exit for root
if [[ ${current_uid} == 0 ]]; then
    exit 0
fi
# Create the user with home dir
useradd -m -d /home/${user_name} -s /bin/bash -g ${current_gid} -u ${current_uid} ${user_name}
