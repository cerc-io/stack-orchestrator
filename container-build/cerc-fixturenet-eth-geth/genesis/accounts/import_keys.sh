#!/bin/sh

ACCOUNT_PASSWORD=${ACCOUNT_PASSWORD:-secret1212}

for line in `cat accounts.csv`; do
  BIP44_PATH="`echo "$line" | cut -d',' -f1`"
  ADDRESS="`echo "$line" | cut -d',' -f2`"
  PUBLIC_KEY="`echo "$line" | cut -d',' -f3`"
  PRIVATE_KEY="`echo "$line" | cut -d',' -f4`"

  echo "$ACCOUNT_PASSWORD" > .pw.$$
  echo "$PRIVATE_KEY" | sed 's/0x//' > .key.$$

  echo ""
  echo "$ADDRESS"
  geth account import --password .pw.$$ .key.$$
  rm -f .pw.$$ .key.$$
done
