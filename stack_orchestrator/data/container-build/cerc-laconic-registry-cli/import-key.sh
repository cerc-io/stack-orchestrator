#!/bin/sh
sed 's/REPLACE_WITH_MYKEY/'${1}'/' registry-cli-config-template.yml > config.yml
