#!/bin/sh
# Offline tests for host-metrics telegraf-entrypoint.sh.
# Stubs telegraf and envsubst's downstream consumer; no telegraf binary needed.
set -eu

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
ENTRYPOINT="$SCRIPT_DIR/telegraf-entrypoint.sh"

[ -x "$ENTRYPOINT" ] || { echo "FATAL: $ENTRYPOINT not executable"; exit 2; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/etc/telegraf"

# Stub telegraf so `exec telegraf` is a no-op.
cat > "$TMP/bin/telegraf" <<'EOF'
#!/bin/sh
exit 0
EOF
chmod +x "$TMP/bin/telegraf"

# Minimal template that exercises both markers.
cat > "$TMP/etc/telegraf/telegraf.conf.tpl" <<'EOF'
@@HOST_TAG_BLOCK@@

[agent]
  interval = "${COLLECT_INTERVAL}"

[[outputs.influxdb]]
  urls = ["${INFLUXDB_URL}"]

@@ZFS_BLOCK@@
EOF

PASS=0
FAIL=0

# run sets required env defaults, then layers caller env on top.
run() {
    env PATH="$TMP/bin:$PATH" \
        TELEGRAF_CONF_DIR="$TMP/etc/telegraf" \
        INFLUXDB_URL="${INFLUXDB_URL-http://example/}" \
        INFLUXDB_USER="${INFLUXDB_USER-writer}" \
        INFLUXDB_PASSWORD="${INFLUXDB_PASSWORD-secret}" \
        INFLUXDB_DB="${INFLUXDB_DB-host_metrics}" \
        COLLECT_INTERVAL="${COLLECT_INTERVAL-10s}" \
        HOST_TAG="${HOST_TAG-}" \
        COLLECT_ZFS="${COLLECT_ZFS-false}" \
        sh "$ENTRYPOINT" >/dev/null
    rc=$?
    [ -f "$TMP/etc/telegraf/telegraf.conf" ] && cat "$TMP/etc/telegraf/telegraf.conf"
    return $rc
}

assert_grep() {
    name=$1; actual=$2; pattern=$3
    if printf '%s' "$actual" | grep -qE "$pattern"; then
        echo "PASS: $name"; PASS=$((PASS + 1))
    else
        echo "FAIL: $name"
        echo "  expected pattern: $pattern"
        echo "  actual: $actual"
        FAIL=$((FAIL + 1))
    fi
}

assert_not_grep() {
    name=$1; actual=$2; pattern=$3
    if printf '%s' "$actual" | grep -qE "$pattern"; then
        echo "FAIL: $name (matched pattern $pattern)"; FAIL=$((FAIL + 1))
    else
        echo "PASS: $name"; PASS=$((PASS + 1))
    fi
}

# T1: HOST_TAG unset -> no [global_tags] block emitted
out=$(HOST_TAG="" run)
assert_not_grep "T1: HOST_TAG empty -> no global_tags" "$out" '^\[global_tags\]'

# T2: HOST_TAG set -> [global_tags] block with host = "<value>"
out=$(HOST_TAG="validator-1" run)
assert_grep "T2: HOST_TAG set -> [global_tags] block" "$out" '^\[global_tags\]'
assert_grep "T2: HOST_TAG set -> host = \"validator-1\"" "$out" 'host = "validator-1"'

# T3: COLLECT_ZFS=true -> [[inputs.zfs]] block present
out=$(COLLECT_ZFS="true" run)
assert_grep "T3: COLLECT_ZFS true -> inputs.zfs block" "$out" '\[\[inputs\.zfs\]\]'

# T4: COLLECT_ZFS=false -> no inputs.zfs block
out=$(COLLECT_ZFS="false" run)
assert_not_grep "T4: COLLECT_ZFS false -> no inputs.zfs" "$out" '\[\[inputs\.zfs\]\]'

# T5: markers fully removed even when block bodies are empty
out=$(HOST_TAG="" COLLECT_ZFS="false" run)
assert_not_grep "T5: no leftover @@HOST_TAG_BLOCK@@" "$out" '@@HOST_TAG_BLOCK@@'
assert_not_grep "T5: no leftover @@ZFS_BLOCK@@" "$out" '@@ZFS_BLOCK@@'

# T6: missing INFLUXDB_URL -> exit non-zero, error on stderr
rc=0
INFLUXDB_URL="" run 2>"$TMP/err" || rc=$?
[ "$rc" -ne 0 ] && grep -q INFLUXDB_URL "$TMP/err" \
    && { echo "PASS: T6: missing INFLUXDB_URL -> error"; PASS=$((PASS + 1)); } \
    || { echo "FAIL: T6: missing INFLUXDB_URL handling (rc=$rc)"; FAIL=$((FAIL + 1)); }

# T7: missing INFLUXDB_USER -> exit non-zero
rc=0
INFLUXDB_USER="" run 2>"$TMP/err" || rc=$?
[ "$rc" -ne 0 ] && grep -q INFLUXDB_USER "$TMP/err" \
    && { echo "PASS: T7: missing INFLUXDB_USER -> error"; PASS=$((PASS + 1)); } \
    || { echo "FAIL: T7: missing INFLUXDB_USER handling (rc=$rc)"; FAIL=$((FAIL + 1)); }

# T8: missing INFLUXDB_PASSWORD -> exit non-zero
rc=0
INFLUXDB_PASSWORD="" run 2>"$TMP/err" || rc=$?
[ "$rc" -ne 0 ] && grep -q INFLUXDB_PASSWORD "$TMP/err" \
    && { echo "PASS: T8: missing INFLUXDB_PASSWORD -> error"; PASS=$((PASS + 1)); } \
    || { echo "FAIL: T8: missing INFLUXDB_PASSWORD handling (rc=$rc)"; FAIL=$((FAIL + 1)); }

echo
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" = "0" ]
