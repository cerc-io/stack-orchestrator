#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

# Verify that we have the config variables we need
if [[ -z ${LACONIC_LACONICD_API_URL} ]]; then
    echo "Error: LACONIC_LACONICD_API_URL not defined"
    exit 1
fi
if [[ -z ${LACONIC_LACONICD_RPC_URL} ]]; then
    echo "Error: LACONIC_LACONICD_RPC_URL not defined"
    exit 1
fi
if [[ -z ${LACONIC_LACONICD_CHAIN_ID} ]]; then
    echo "Error: LACONIC_LACONICD_CHAIN_ID not defined"
    exit 1
fi

explorer_config_dir=/app/chains/mainnet
config_template_file=/config/chains/mainnet/laconic-chaindata-template.json
config_file=${explorer_config_dir}/laconic.json

# Delete the stock config files
rm -f ${explorer_config_dir}/*

# Copy in our template file
cp ${config_template_file} ${config_file}

# Update the file with the config variables
sed -i "s#LACONIC_LACONICD_API_URL#${LACONIC_LACONICD_API_URL}#g" ${config_file}
sed -i "s#LACONIC_LACONICD_RPC_URL#${LACONIC_LACONICD_RPC_URL}#g" ${config_file}
sed -i "s#LACONIC_LACONICD_CHAIN_ID#${LACONIC_LACONICD_CHAIN_ID}#g" ${config_file}

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  echo "Updated chaindata file:"
  cat ${config_file}
fi
