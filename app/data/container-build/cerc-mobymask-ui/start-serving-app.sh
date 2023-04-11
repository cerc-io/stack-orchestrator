#!/usr/bin/env bash
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi
# TODO: Don't hard wire this:
webapp_files_dir=/app/build
/scripts/apply-webapp-config.sh /config/config.yml ${webapp_files_dir} MOBYMASK_HOSTED_CONFIG
http-server -p 80 ${webapp_files_dir}
