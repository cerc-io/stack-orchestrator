#!/bin/sh
# Restart a container by label filter
# Used by the cron-based restarter sidecar
label_filter="$1"
container=$(docker ps -qf "label=$label_filter")
if [ -n "$container" ]; then
  docker restart -s TERM "$container" > /dev/null
fi
