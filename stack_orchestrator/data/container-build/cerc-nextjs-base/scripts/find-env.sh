#!/bin/bash

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

WORK_DIR="${1:-./}"
TMPF=$(mktemp)

cd "$WORK_DIR" || exit 1

for d in $(find . -maxdepth 1 -type d | grep -v '\./\.' | grep '/' | cut -d'/' -f2); do
  egrep "/$d[/$]?" .gitignore >/dev/null 2>/dev/null
  if [ $? -eq 0 ]; then
    continue
  fi

  for f in $(find "$d" -regex ".*.[tj]sx?$" -type f); do
    cat "$f" | tr -s '[:blank:]' '\n' | tr -s '[{},()]' '\n' | egrep -o 'process.env.[A-Za-z0-9_]+' >> $TMPF
  done
done

cat $TMPF | sort -u | jq  --raw-input .  | jq --slurp .
rm -f $TMPF
