#!/bin/sh
# host-metrics telegraf-entrypoint.sh
# Render telegraf.conf from telegraf.conf.tpl, then exec telegraf.
#
# Substitutions performed here (by awk):
#   @@HOST_TAG_BLOCK@@ -> "[global_tags]\n  host = \"$HOST_TAG\"" if set, else empty.
#   @@ZFS_BLOCK@@      -> "[[inputs.zfs]]\n  poolMetrics = true"  if COLLECT_ZFS=true, else empty.
#
# Variables of the form ${VAR} in the template (INFLUXDB_URL, INFLUXDB_DB,
# INFLUXDB_USER, INFLUXDB_PASSWORD, COLLECT_INTERVAL) are resolved by
# telegraf's own env-var substitution at config-load time and are NOT
# touched by this script.
#
# TELEGRAF_CONF_DIR overrides the conf directory for tests; defaults to
# /etc/telegraf which is the standard path inside the official image.

set -eu

CONF_DIR="${TELEGRAF_CONF_DIR:-/etc/telegraf}"
TPL="$CONF_DIR/telegraf.conf.tpl"
OUT="$CONF_DIR/telegraf.conf"

# Fail-fast required env. Empty string counts as missing -- a half-rendered
# conf or a noisy telegraf auth error is worse than a clear startup failure.
for v in INFLUXDB_URL INFLUXDB_USER INFLUXDB_PASSWORD; do
    eval val=\${$v:-}
    if [ -z "$val" ]; then
        echo "FATAL: $v is required but empty" >&2
        exit 1
    fi
done

# Apply defaults for optional vars.
: "${INFLUXDB_DB:=host_metrics}"
: "${COLLECT_INTERVAL:=10s}"
: "${HOST_TAG:=}"
: "${COLLECT_ZFS:=false}"

# Build the marker substitutions. Use printf for the newline so the
# rendered block lands on its own line.
if [ -n "$HOST_TAG" ]; then
    HOST_TAG_BLOCK=$(printf '[global_tags]\n  host = "%s"' "$HOST_TAG")
else
    HOST_TAG_BLOCK=""
fi

if [ "$COLLECT_ZFS" = "true" ]; then
    ZFS_BLOCK=$(printf '[[inputs.zfs]]\n  poolMetrics = true')
else
    ZFS_BLOCK=""
fi

# Export telegraf hostfs envs so /proc, /sys, and root come from the
# bind-mount under /hostfs (set in compose).
export HOST_PROC=/hostfs/proc
export HOST_SYS=/hostfs/sys
export HOST_MOUNT_PREFIX=/hostfs

# Render with awk: handles multi-line replacement values cleanly,
# avoids sed's newline-in-replacement portability quirks across BusyBox /
# GNU / BSD sed.
awk -v ht="$HOST_TAG_BLOCK" -v zb="$ZFS_BLOCK" '
    { gsub(/@@HOST_TAG_BLOCK@@/, ht);
      gsub(/@@ZFS_BLOCK@@/, zb);
      print }
' "$TPL" > "$OUT"

exec telegraf --config "$OUT"
