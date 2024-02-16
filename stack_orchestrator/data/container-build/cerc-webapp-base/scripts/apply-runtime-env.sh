#!/bin/bash

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

WORK_DIR="${1:-./}"

cd "${WORK_DIR}" || exit 1

if [ -f ".env" ]; then
  TMP_ENV=`mktemp`
  declare -px > $TMP_ENV
  set -a
  source .env
  source $TMP_ENV
  set +a
  rm -f $TMP_ENV
fi


for f in $(find . -type f \( -name '*.html' -or -regex ".*.[tj]s\(x\|on\)?$" \) | grep -v 'node_modules' | grep -v '.git'); do
  for e in $(cat "${f}" | tr -s '[:blank:]' '\n' | tr -s '[\\/{},();"]' '\n' | egrep -o -e '^CERC_RUNTIME_ENV_.+'); do
    orig_name=$(echo -n "${e}" | sed 's/"//g')
    cur_name=$(echo -n "${orig_name}" | sed 's/CERC_RUNTIME_ENV_//g')
    cur_val=$(echo -n "\$${cur_name}" | envsubst)
    if [ "$CERC_RETAIN_ENV_QUOTES" != "true" ]; then
      cur_val=$(sed "s/^[\"']//" <<< "$cur_val" | sed "s/[\"']//")
    fi
    esc_val=$(sed 's/[&/\]/\\&/g' <<< "$cur_val")
    echo "$f: $cur_name=$cur_val"
    sed -i "s/$orig_name/$esc_val/g" $f
  done
done

for f in $(find . -type f \( -name '*.html' -or -regex ".*.[tj]s\(x\|on\)?$" \) | grep -v 'node_modules' | grep -v '.git'); do
  for cur_name in `env | egrep -o -e '^LACONIC_HOSTED_CONFIG_.+' | cut -d"=" -f1 | sort -u`; do
    grep "$e" $f >/dev/null
    if [ $? -ne 0 ]; then
      continue
    fi
    cur_val=$(echo -n "\$${cur_name}" | envsubst)
    if [ "$CERC_RETAIN_ENV_QUOTES" != "true" ]; then
      cur_val=$(sed "s/^[\"']//" <<< "$cur_val" | sed "s/[\"']//")
    fi
    esc_val=$(sed 's/[&/\]/\\&/g' <<< "$cur_val")
    echo "$f: $cur_name=$cur_val"
    sed -i "s/$cur_name/$esc_val/g" $f
  done
done
