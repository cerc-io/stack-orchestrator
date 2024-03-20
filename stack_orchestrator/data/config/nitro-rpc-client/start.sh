#!/bin/bash

CERC_NITRO_RPC_FUND_AMOUNT=${CERC_NITRO_RPC_FUND_AMOUNT:-0}
CERC_NITRO_RPC_HOST_ALICE=${CERC_NITRO_RPC_HOST_ALICE:-go-nitro-alice}
CERC_NITRO_RPC_PORT_ALICE=${CERC_NITRO_RPC_PORT_ALICE:-4006}
CERC_NITRO_USE_TLS=${CERC_NITRO_USE_TLS:-false}
CERC_NITRO_ADDRESS_BOB=${CERC_NITRO_ADDRESS_BOB:-0xe07e314501cc73b24cf45a6577486017300e153c}


# Wait till chain endpoint is available
retry_interval=5
while true; do
  nc -z -w 1 "$CERC_NITRO_RPC_HOST_ALICE" "$CERC_NITRO_RPC_PORT_ALICE"

  if [ $? -eq 0 ]; then
    echo "Nitro endpoint is available"
    break
  fi

  echo "Nitro endpoint not yet available, retrying in $retry_interval seconds..."
  sleep $retry_interval
done

if [[ "$CERC_NITRO_RPC_FUND_AMOUNT" -gt 0 ]]; then
  nitro-rpc-client -h $CERC_NITRO_RPC_HOST_ALICE \
                   -p $CERC_NITRO_RPC_PORT_ALICE \
                   -s=$CERC_NITRO_USE_TLS \
                   get-all-ledger-channels | \
                     jq "[.[] | select(.Status == \"Open\") | select(.Balance.Them == \"$CERC_NITRO_ADDRESS_BOB\")] | first" > \
                     /app/deployment/nitro-ledger-channel-alice-to-bob.json

  ledger_channel=$(jq -r '.ID' /app/deployment/nitro-ledger-channel-alice-to-bob.json 2>/dev/null | sed 's/^null$//')

  if [[ -z "${ledger_channel}" ]]; then
    echo "Creating new ledger channel ..."
    nitro-rpc-client -h $CERC_NITRO_RPC_HOST_ALICE \
                     -p $CERC_NITRO_RPC_PORT_ALICE \
                     -s=$CERC_NITRO_USE_TLS \
                     -n \
                     direct-fund --amount $CERC_NITRO_RPC_FUND_AMOUNT $CERC_NITRO_ADDRESS_BOB

    nitro-rpc-client -h $CERC_NITRO_RPC_HOST_ALICE \
                     -p $CERC_NITRO_RPC_PORT_ALICE \
                     -s=$CERC_NITRO_USE_TLS \
                     get-all-ledger-channels | \
                       jq "[.[] | select(.Status == \"Open\") | select(.Balance.Them == \"$CERC_NITRO_ADDRESS_BOB\")] | first" > \
                       /app/deployment/nitro-ledger-channel-alice-to-bob.json

    ledger_channel=$(jq -r '.ID' /app/deployment/nitro-ledger-channel-alice-to-bob.json)
  fi

  nitro-rpc-client -h $CERC_NITRO_RPC_HOST_ALICE \
                   -p $CERC_NITRO_RPC_PORT_ALICE \
                   -s=$CERC_NITRO_USE_TLS \
                   get-payment-channels-by-ledger $ledger_channel > \
                     /app/deployment/nitro-payment-channels-alice-to-bob.json

  first_open_channel=$(jq '[.[] | select(.Status == "Open")] | first' /app/deployment/nitro-payment-channels-alice-to-bob.json | sed 's/^null$//')

  if [[ -z "$first_open_channel" ]]; then
    echo "Creating new payment channel ..."
    nitro-rpc-client -h $CERC_NITRO_RPC_HOST_ALICE \
                     -p $CERC_NITRO_RPC_PORT_ALICE \
                     -s=$CERC_NITRO_USE_TLS \
                     -n \
                     virtual-fund --amount $((CERC_NITRO_RPC_FUND_AMOUNT/2)) $CERC_NITRO_ADDRESS_BOB

    nitro-rpc-client -h $CERC_NITRO_RPC_HOST_ALICE \
                     -p $CERC_NITRO_RPC_PORT_ALICE \
                     -s=$CERC_NITRO_USE_TLS \
                     get-payment-channels-by-ledger $ledger_channel > \
                       /app/deployment/nitro-payment-channels-alice-to-bob.json

    first_open_channel=$(jq '[.[] | select(.Status == "Open")] | first' /app/deployment/nitro-payment-channels-alice-to-bob.json | sed 's/^null$//')
  fi

  echo ""
  echo "################################################################"
  echo ""

  echo "LEDGER:"
  cat /app/deployment/nitro-ledger-channel-alice-to-bob.json | jq
  echo ""
  echo ""

  echo "PAYMENT:"
  cat /app/deployment/nitro-payment-channels-alice-to-bob.json | jq
  echo ""
  echo ""
fi

if [ -n "$1" ]; then
  exec "$@"
  exit $?
fi

while [ 1 -eq 1 ]; do
  sleep 100
done
