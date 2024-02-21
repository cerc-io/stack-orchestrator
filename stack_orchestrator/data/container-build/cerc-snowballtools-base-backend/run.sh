#!/bin/bash


LACONIC_HOSTED_CONFIG_FILE=${LACONIC_HOSTED_CONFIG_FILE}
if [ -z "${LACONIC_HOSTED_CONFIG_FILE}" ]; then
  if [ -f "/config/laconic-hosted-config.yml" ]; then
    LACONIC_HOSTED_CONFIG_FILE="/config/laconic-hosted-config.yml"
  elif [ -f "/config/config.yml" ]; then
    LACONIC_HOSTED_CONFIG_FILE="/config/config.yml"
  fi
fi

if [ -f "${LACONIC_HOSTED_CONFIG_FILE}" ]; then
  /scripts/apply-webapp-config.sh $LACONIC_HOSTED_CONFIG_FILE "`pwd`/dist"
fi

/scripts/apply-runtime-env.sh "`pwd`/dist"

yarn start
