#!/bin/sh
sed 's/REPLACE_WITH_MYKEY/'${1}'/' mobymask-secrets-template.json > secrets.json
