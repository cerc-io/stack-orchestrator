#!/bin/bash
# Make the container usable for uid/gid != 1000
if [[ -n "$CERC_SCRIPT_DEBUG" ]]; then
    set -x
fi
current_uid=$(id -u)
current_gid=$(id -g)
# Don't check if running as root
if [[ ${current_uid} == 0 ]]; then
    exit 0
fi
# Check the current uid/gid vs the uid/gid used to build the container.
# We do this because both bind mounts and npm tooling require the uid/gid to match.
if [[ ${current_gid} != ${HOST_GID} ]]; then
    echo "Warning: running with gid: ${current_gid} which is not the gid for which this container was built (${HOST_GID})"
    exit 0
fi
if [[ ${current_uid} != ${HOST_UID} ]]; then
    echo "Warning: running with gid: ${current_uid} which is not the uid for which this container was built (${HOST_UID})"
    exit 0
fi
