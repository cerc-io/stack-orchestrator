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

# Ping-pub explorer has endlessly confusing behavior where it
# infers the directory from which to load chain configuration files
# by the presence or absense of the substring "testnet" in the host name
# (browser side -- the host name of the host in the address bar of the browser)
# Accordingly we configure our network in both directories in order to 
# subvert this lunacy.
explorer_mainnet_config_dir=/app/chains/mainnet
explorer_testnet_config_dir=/app/chains/testnet
config_template_file=/config/chains/laconic-chaindata-template.json
chain_config_name=laconic.json
mainnet_config_file=${explorer_mainnet_config_dir}/${chain_config_name}
testnet_config_file=${explorer_testnet_config_dir}/${chain_config_name}

# Delete the stock config files
rm -f ${explorer_testnet_config_dir}/*
rm -f ${explorer_mainnet_config_dir}/*

# Copy in our template file
cp ${config_template_file} ${mainnet_config_file}

# Update the file with the config variables
sed -i "s#LACONIC_LACONICD_API_URL#${LACONIC_LACONICD_API_URL}#g" ${mainnet_config_file}
sed -i "s#LACONIC_LACONICD_RPC_URL#${LACONIC_LACONICD_RPC_URL}#g" ${mainnet_config_file}
sed -i "s#LACONIC_LACONICD_CHAIN_ID#${LACONIC_LACONICD_CHAIN_ID}#g" ${mainnet_config_file}

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  echo "Updated chaindata file:"
  cat ${mainnet_config_file}
fi

# Copy over to the testnet directory
cp ${mainnet_config_file} ${testnet_config_file}
