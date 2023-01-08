#!/bin/bash

LIGHTHOUSE_BASE_URL=http://localhost:8001

result=`wget --no-check-certificate --quiet -O - "$LIGHTHOUSE_BASE_URL/eth/v2/beacon/blocks/head" | jq -r '.data.message.body.execution_payload.block_number'`
if [ ! -z "$result" ] && [ $result -gt 0 ]; then
  exit 0
fi

exit 1
