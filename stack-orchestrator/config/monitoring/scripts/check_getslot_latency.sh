#!/bin/bash
# Check getSlot RPC latency
# Outputs metrics in InfluxDB line protocol format

set -euo pipefail

RPC_URL="${NODE_RPC_URL:-http://localhost:8899}"
RPC_PAYLOAD='{"jsonrpc":"2.0","id":1,"method":"getSlot"}'

response=$(curl -sk --max-time 10 -X POST \
  -H "Content-Type: application/json" \
  -d "$RPC_PAYLOAD" \
  -w "\n%{http_code}\n%{time_total}" \
  "$RPC_URL" 2>/dev/null || echo -e "\n000\n0")

json_response=$(echo "$response" | head -n 1)
# curl -w output follows response body; blank lines may appear between them
http_code=$(echo "$response" | tail -2 | head -1)
time_total=$(echo "$response" | tail -1)

latency_ms="$(awk -v t="$time_total" 'BEGIN { printf "%.0f", (t * 1000) }')"
# Strip leading zeros from http_code (influx line protocol rejects 000i)
http_code=$((10#${http_code:-0}))

if [ "$http_code" = "200" ]; then
  slot=$(echo "$json_response" | grep -o '"result":[0-9]*' | grep -o '[0-9]*' || echo "0")
  [ "$slot" != "0" ] && success=1 || success=0
else
  success=0
  slot=0
fi

echo "rpc_latency,endpoint=direct,method=getSlot latency_ms=${latency_ms},success=${success}i,http_code=${http_code}i,slot=${slot}i"
