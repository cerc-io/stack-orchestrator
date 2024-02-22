#!/usr/bin/env bash
set -e

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "Test container starting"

DATA_DEVICE=$(df | grep "/data$" | awk '{ print $1 }')
if [[ -n "$DATA_DEVICE" ]]; then
  echo "/data: MOUNTED dev=${DATA_DEVICE}"
else
  echo "/data: not mounted"
fi

DATA2_DEVICE=$(df | grep "/data2$" | awk '{ print $1 }')
if [[ -n "$DATA_DEVICE" ]]; then
  echo "/data2: MOUNTED dev=${DATA2_DEVICE}"
else
  echo "/data2: not mounted"
fi

# Test if the container's filesystem is old (run previously) or new
for d in /data /data2; do
  if [[ -f "$d/exists" ]];
  then
      TIMESTAMP=`cat $d/exists`
      echo "$d filesystem is old, created: $TIMESTAMP"
  else
      echo "$d filesystem is fresh"
      echo `date` > $d/exists
  fi
done

if [ -n "$CERC_TEST_PARAM_1" ]; then
  echo "Test-param-1: ${CERC_TEST_PARAM_1}"
fi
if [ -n "$CERC_TEST_PARAM_2" ]; then
  echo "Test-param-2: ${CERC_TEST_PARAM_2}"
fi
if [ -n "$CERC_TEST_PARAM_3" ]; then
  echo "Test-param-3: ${CERC_TEST_PARAM_3}"
fi
if [ -n "$CERC_TEST_PARAM_4" ]; then
  echo "Test-param-4: ${CERC_TEST_PARAM_4}"
fi
if [ -n "$CERC_TEST_PARAM_5" ]; then
  echo "Test-param-5: ${CERC_TEST_PARAM_5}"
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
