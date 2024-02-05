#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi
# Test if the container's filesystem is old (run previously) or new
EXISTSFILENAME=/data/exists
echo "Test container starting"
if [[ -f "$EXISTSFILENAME" ]];
then
    TIMESTAMP=`cat $EXISTSFILENAME`
    echo "Filesystem is old, created: $TIMESTAMP" 
else
    echo "Filesystem is fresh"
    echo `date` > $EXISTSFILENAME
fi
if [ -n "$CERC_TEST_PARAM_1" ]; then
  echo "Test-param-1: ${CERC_TEST_PARAM_1}"
fi

if [ -d "/config" ]; then
  echo "/config: EXISTS"
  for f in /config/*; do
    if [[ -f "$f" ]] || [[ -L "$f" ]]; then
      echo "$f:"
      cat "$f"
      echo ""
      echo ""
    fi
  done
else
  echo "/config: does NOT EXIST"
fi

# Run nginx which will block here forever
/usr/sbin/nginx -g "daemon off;"
