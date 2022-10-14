#!/usr/bin/env bash

#
# Deploys the deposit contract and makes deposits for $VALIDATOR_COUNT insecure deterministic validators.
# Produces a testnet specification and a genesis state where the genesis time
# is now + $GENESIS_DELAY.
#
# Generates datadirs for multiple validator keys according to the
# $VALIDATOR_COUNT and $BN_COUNT variables.
#

set -o nounset -o errexit -o pipefail

source ./vars.env

rm -rf $DATADIR
mkdir -p $DATADIR

NOW=`date +%s`
GENESIS_TIME=`expr $NOW + $GENESIS_DELAY`

echo "Creating testnet ..."
lcli \
  new-testnet \
  --spec $SPEC_PRESET \
  --deposit-contract-address $ETH1_DEPOSIT_CONTRACT_ADDRESS \
  --testnet-dir $TESTNET_DIR \
  --min-genesis-active-validator-count $GENESIS_VALIDATOR_COUNT \
  --min-genesis-time $GENESIS_TIME \
  --genesis-delay $GENESIS_DELAY \
  --genesis-fork-version $GENESIS_FORK_VERSION \
  --altair-fork-epoch $ALTAIR_FORK_EPOCH \
  --merge-fork-epoch $MERGE_FORK_EPOCH \
  --eth1-id $ETH1_CHAIN_ID \
  --eth1-follow-distance 1 \
  --seconds-per-slot $SECONDS_PER_SLOT \
  --seconds-per-eth1-block $SECONDS_PER_ETH1_BLOCK \
  --force

echo Specification generated at $TESTNET_DIR.
echo "Generating $VALIDATOR_COUNT validators concurrently... (this may take a while)"

lcli \
  insecure-validators \
  --count $VALIDATOR_COUNT \
  --base-dir $DATADIR \
  --node-count $BN_COUNT

echo Validators generated with keystore passwords at $DATADIR.
echo "Building genesis state... (this might take a while)"

lcli \
  interop-genesis \
  --spec $SPEC_PRESET \
  --genesis-time $GENESIS_TIME \
  --testnet-dir $TESTNET_DIR \
  $GENESIS_VALIDATOR_COUNT

echo Created genesis state in $TESTNET_DIR

echo "Generating bootnode enr"

lcli \
  generate-bootnode-enr \
  --ip $BOOTNODE_IP \
  --udp-port $BOOTNODE_PORT \
  --tcp-port $BOOTNODE_PORT \
  --genesis-fork-version $GENESIS_FORK_VERSION \
  --output-dir $DATADIR/bootnode

bootnode_enr=`cat $DATADIR/bootnode/enr.dat`
echo "- $bootnode_enr" > $TESTNET_DIR/boot_enr.yaml

echo "Generated bootnode enr and written to $TESTNET_DIR/boot_enr.yaml"
