#!/usr/bin/env bash
# Test procedure for shred-relay containerlab topology.
#
# Prerequisites:
#   sudo containerlab deploy -t topology.yml
#
# This script configures the alpine containers and runs the end-to-end
# redirect test. Run from the shred-relay-lab/ directory.

set -euo pipefail

LAB_PREFIX="clab-shred-relay"

echo "=== Configuring biscayne ==="
sudo docker exec "$LAB_PREFIX-biscayne" sh -c '
  ip addr add 172.16.1.189/31 dev eth1
  ip addr add 186.233.184.235/32 dev lo
  ip route add default via 172.16.1.188
'

echo "=== Configuring turbine-src ==="
sudo docker exec "$LAB_PREFIX-turbine-src" sh -c '
  ip addr add 10.0.1.2/24 dev eth1
  ip route add default via 64.92.84.81
'

echo "=== Starting UDP listener on biscayne:20000 ==="
sudo docker exec -d "$LAB_PREFIX-biscayne" sh -c '
  nc -ul -p 20000 > /tmp/received.txt &
'
sleep 1

echo "=== Sending test shred from turbine-src to 64.92.84.81:20000 ==="
sudo docker exec "$LAB_PREFIX-turbine-src" sh -c '
  echo "SHRED_PAYLOAD_TEST" | nc -u -w1 64.92.84.81 20000
'
sleep 2

echo "=== Checking biscayne received the payload ==="
RECEIVED=$(sudo docker exec "$LAB_PREFIX-biscayne" cat /tmp/received.txt 2>/dev/null || true)
if echo "$RECEIVED" | grep -q "SHRED_PAYLOAD_TEST"; then
  echo "PASS: biscayne received redirected shred payload"
else
  echo "FAIL: payload not received on biscayne (got: '$RECEIVED')"
fi

echo ""
echo "=== Checking traffic-policy counters on was-sw01 ==="
sudo docker exec "$LAB_PREFIX-was-sw01" Cli -c "show traffic-policy counters" 2>/dev/null || \
  echo "(traffic-policy counters not available on cEOS)"

echo ""
echo "=== Verifying ping still works (non-redirected traffic) ==="
sudo docker exec "$LAB_PREFIX-turbine-src" ping -c 2 -W 2 64.92.84.81 && \
  echo "PASS: ICMP to switch still works" || \
  echo "FAIL: ICMP to switch broken"

echo ""
echo "=== Bonus: DNAT test (64.92.84.81:20000 -> 127.0.0.1:9000) ==="
sudo docker exec "$LAB_PREFIX-biscayne" sh -c '
  apk add --no-cache iptables 2>/dev/null
  iptables -t nat -A PREROUTING -p udp -d 64.92.84.81 --dport 20000 -j DNAT --to-destination 127.0.0.1:9000
  nc -ul -p 9000 > /tmp/dnat-received.txt &
'
sleep 1

sudo docker exec "$LAB_PREFIX-turbine-src" sh -c '
  echo "DNAT_TEST_PAYLOAD" | nc -u -w1 64.92.84.81 20000
'
sleep 2

DNAT_RECEIVED=$(sudo docker exec "$LAB_PREFIX-biscayne" cat /tmp/dnat-received.txt 2>/dev/null || true)
if echo "$DNAT_RECEIVED" | grep -q "DNAT_TEST_PAYLOAD"; then
  echo "PASS: DNAT redirect to localhost:9000 works"
else
  echo "FAIL: DNAT payload not received (got: '$DNAT_RECEIVED')"
fi
