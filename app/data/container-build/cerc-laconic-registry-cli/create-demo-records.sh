#!/usr/bin/env bash
# Create some demo/test records in the registry
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

registry_command="laconic cns"
demo_records_dir="demo-records"

# Check we have funds
funds_response=$(${registry_command} account get --address $(cat my-address.txt))
funds_balance=$(echo ${funds_response} | jq -r .[0].balance[0].quantity)
echo "Balance is: ${funds_balance}"

# Create a bond
bond_create_result=$(${registry_command} bond create --type aphoton --quantity 1000000000)
bond_id=$(echo ${bond_create_result} | jq -r .bondId)
echo "Created bond with id: ${bond_id}"

## Publish the demo records
if [ -d $demo_records_dir ]; then
  for demo_record in "${demo_records_dir}"/*; do
    publish_response=$(${registry_command} record publish --filename ${demo_record} --bond-id ${bond_id})
    published_record_id=$(echo ${publish_response} | jq -r .id)
    echo "Published ${demo_record} with id: ${published_record_id}"
    cat ${demo_record}
  done
fi
