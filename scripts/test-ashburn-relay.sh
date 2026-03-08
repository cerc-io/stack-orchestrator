#!/usr/bin/env bash
# End-to-end test for Ashburn validator relay
#
# Sends real packets from the kind node through the full relay path
# and waits for responses. A response proves both directions work.
#
#   Outbound: kind node (172.20.0.2:8001) → biscayne mangle (fwmark 0x64)
#     → policy route table ashburn → gre-ashburn → mia-sw01 Tunnel100
#     (VRF relay) → egress-vrf default → backbone Et4/1 → was-sw01 Et1/1
#     → internet (src 137.239.194.65)
#
#   Inbound: internet → was-sw01 Et1/1 (dst 137.239.194.65) → static route
#     → backbone → mia-sw01 → egress-vrf relay → Tunnel100 → biscayne
#     gre-ashburn → conntrack reverse-SNAT → kind node (172.20.0.2:8001)
#
# Runs from the ansible controller host.
#
# Usage:
#   ./scripts/test-ashburn-relay.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

KIND_NODE=laconic-70ce4c4b47e23b85-control-plane
BISCAYNE_INV=inventory/biscayne.yml
GOSSIP_PORT=8001

PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

# Copy test scripts to biscayne (once)
setup() {
  for f in "$SCRIPT_DIR"/relay-test-*.py; do
    ansible biscayne -i "$BISCAYNE_INV" -m ansible.builtin.copy \
      -a "src=$f dest=/tmp/$(basename "$f") mode=0755" \
      --become >/dev/null 2>&1
  done

  # Get kind node PID for nsenter (run in its network namespace,
  # use biscayne's python3 since the kind node only has perl)
  KIND_PID=$(ansible biscayne -i "$BISCAYNE_INV" -m ansible.builtin.shell \
    -a "docker inspect --format '{{ '{{' }}.State.Pid{{ '}}' }}' $KIND_NODE" \
    --become 2>&1 | grep -oP '^\d+$' || true)

  if [[ -z "$KIND_PID" ]]; then
    echo "FATAL: could not get kind node PID"
    exit 1
  fi
  echo "Kind node PID: $KIND_PID"
}

# Run a test script in the kind node's network namespace
run_test() {
  local name=$1
  shift
  ansible biscayne -i "$BISCAYNE_INV" -m ansible.builtin.shell \
    -a "nsenter --net --target $KIND_PID python3 /tmp/$name $*" \
    --become 2>&1 | grep -E '^OK|^TIMEOUT|^ERROR|^REFUSED|^NOTE|^FAIL' || echo "NO OUTPUT"
}

echo "=== Ashburn Relay End-to-End Test ==="
echo ""

setup
echo ""

# Test 1: UDP sport 8001 → DNS query to 8.8.8.8
# Triggers: mangle -p udp --sport 8001 → mark → SNAT → tunnel
echo "--- Test 1: UDP sport $GOSSIP_PORT (DNS query) ---"
result=$(run_test relay-test-udp.py "$GOSSIP_PORT")
if echo "$result" | grep -q "^OK"; then
  pass "UDP sport $GOSSIP_PORT: $result"
else
  fail "UDP sport $GOSSIP_PORT: $result"
fi
echo ""

# Test 2: TCP sport 8001 → HTTP HEAD to 1.1.1.1
# Triggers: mangle -p tcp --sport 8001 → mark → SNAT → tunnel
echo "--- Test 2: TCP sport $GOSSIP_PORT (HTTP request) ---"
result=$(run_test relay-test-tcp-sport.py "$GOSSIP_PORT")
if echo "$result" | grep -q "^OK"; then
  pass "TCP sport $GOSSIP_PORT: $result"
else
  fail "TCP sport $GOSSIP_PORT: $result"
fi
echo ""

# Test 3: TCP dport 8001 → connect to Solana entrypoint (ip_echo)
# Triggers: mangle -p tcp --dport 8001 → mark → SNAT → tunnel
# REFUSED counts as pass — proves the round trip completed.
echo "--- Test 3: TCP dport $GOSSIP_PORT (ip_echo path) ---"
result=$(run_test relay-test-tcp-dport.py "$GOSSIP_PORT")
if echo "$result" | grep -q "^OK"; then
  pass "TCP dport $GOSSIP_PORT: $result"
else
  fail "TCP dport $GOSSIP_PORT: $result"
fi
echo ""

# Test 4: ip_echo UDP reachability — the actual validator startup check
# Sends correct ip_echo protocol to entrypoint, which probes our UDP port.
# This is the path that causes CrashLoopBackOff when broken.
# Triggers: outbound TCP dport 8001 (mangle mark → tunnel → SNAT)
#           inbound UDP dport 8001 (was-sw01 → backbone → mia-sw01 → tunnel → DNAT)
echo "--- Test 4: ip_echo UDP reachability (inbound UDP probe) ---"
result=$(run_test relay-test-ip-echo.py 34.83.231.102 "$GOSSIP_PORT")
if echo "$result" | grep -q "^OK inbound UDP"; then
  pass "ip_echo UDP reachability: $result"
elif echo "$result" | grep -q "^OK"; then
  # Partial success — TCP worked but no UDP probes arrived
  fail "ip_echo partial — no inbound UDP: $result"
else
  fail "ip_echo: $result"
fi
echo ""

# Summary
echo "=== Results: $PASS passed, $FAIL failed ==="
if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
