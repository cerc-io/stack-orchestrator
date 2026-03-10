#!/bin/sh

if [ "$ENABLE_PROXY" = "true" ]; then
  echo "Proxy server enabled"
  yarn proxy
else
  echo "Proxy server disabled, exiting"
  exit 0
fi
