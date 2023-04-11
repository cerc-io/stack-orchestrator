#!/usr/bin/env bash
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi
# TODO: Don't hard wire this:
webapp_files_dir=/usr/local/share/.config/yarn/global/node_modules/@cerc-io/console-app/dist/production
/scripts/apply-webapp-config.sh /config/config.yml ${webapp_files_dir} LACONIC_HOSTED_CONFIG
http-server -p 80 ${webapp_files_dir}
