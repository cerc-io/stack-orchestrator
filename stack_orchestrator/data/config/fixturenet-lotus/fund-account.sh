#!/bin/bash

# ETH account with pk c05fd3613bcd62a4f25e5eba1f464d0b76d74c3f771a7c2f13e26ad6439444b3
ETH_ADDRESS=0xD375B03bd3A2434A9f675bEC4Ccd68aC5e67C743
AMOUNT=1000

# Pre-fund stat
PREFUND_STAT_OUTPUT=$(lotus evm stat $ETH_ADDRESS)

FILECOIN_ADDRESS=$(echo "$PREFUND_STAT_OUTPUT" | grep -oP 'Filecoin address:\s+\K\S+')
echo Filecoin address: "$FILECOIN_ADDRESS"

echo Sending balance to "$FILECOIN_ADDRESS"
lotus send --from $(lotus wallet default) "$FILECOIN_ADDRESS" $AMOUNT

# Post-fund stat
echo lotus evm stat $ETH_ADDRESS
lotus evm stat $ETH_ADDRESS

echo "Account with ETH address $ETH_ADDRESS funded"
