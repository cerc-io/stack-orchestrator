#!/usr/bin/env bash
# Create some demo/test records in the registry
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi
registry_command="laconic cns"
record_1_filename=demo-record-1.yml
cat <<EOF > ${record_1_filename}
record:
  type: WebsiteRegistrationRecord
  url: 'https://cerc.io'
  repo_registration_record_cid: QmSnuWmxptJZdLJpKRarxBMS2Ju2oANVrgbr2xWbie9b2D
  build_artifact_cid: QmP8jTG1m9GSDJLCbeWhVSVgEzCPPwXRdCRuJtQ5Tz9Kc9
  tls_cert_cid: QmbWqxBEKC3P8tqsKc98xmWNzrzDtRLMiMPL8wBuTGsMnR
  version: 1.0.23
EOF
# Check we have funds
funds_response=$(${registry_command} account get --address $(cat my-address.txt))
funds_balance=$(echo ${funds_response} | jq -r .[0].balance[0].quantity)
echo "Balance is: ${funds_balance}"
# Create a bond
bond_create_result=$(${registry_command} bond create --type aphoton --quantity 1000000000)
bond_id=$(echo ${bond_create_result} | jq -r .bondId)
echo "Created bond with id: ${bond_id}"
# Publish a demo record
publish_response=$(${registry_command} record publish --filename ${record_1_filename} --bond-id ${bond_id})
published_record_id=$(echo ${publish_response} | jq -r .id)
echo "Published ${record_1_filename} with id: ${published_record_id}"
