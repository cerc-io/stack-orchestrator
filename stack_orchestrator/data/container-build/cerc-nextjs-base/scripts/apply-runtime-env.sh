#!/bin/bash

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

WORK_DIR="${1:-./}"
SRC_DIR="${2:-.next}"
TRG_DIR="${3:-.next-r}"

cd "${WORK_DIR}" || exit 1

rm -rf "$TRG_DIR"
mkdir -p "$TRG_DIR"
cp -rp "$SRC_DIR" "$TRG_DIR/"

if [ -f ".env" ]; then
  TMP_ENV=`mktemp`
  declare -px > $TMP_ENV
  set -a
  source .env
  source $TMP_ENV
  set +a
  rm -f $TMP_ENV
fi

for f in $(find "$TRG_DIR" -regex ".*.[tj]sx?$" -type f | grep -v 'node_modules'); do
  for e in $(cat "${f}" | tr -s '[:blank:]' '\n' | tr -s '[{},()]' '\n' | egrep -o '^"CERC_RUNTIME_ENV[^\"]+"$'); do
    orig_name=$(echo -n "${e}" | sed 's/"//g')
    cur_name=$(echo -n "${orig_name}" | sed 's/CERC_RUNTIME_ENV_//g')
    cur_val=$(echo -n "\$${cur_name}" | envsubst)
    esc_val=$(sed 's/[&/\]/\\&/g' <<< "$cur_val")
    echo "$cur_name=$cur_val"
    sed -i "s/$orig_name/$esc_val/g" $f
  done
done
