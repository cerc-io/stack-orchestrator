#!/usr/bin/env bash

# See https://github.com/sigp/lighthouse/scripts/local_testnet/setup.sh
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
echo "(Note: errors of the form 'WARN: Scrypt parameters are too weak...' below can be safely ignored)"
lcli \
  new-testnet \
  --spec $SPEC_PRESET \
  --testnet-dir $TESTNET_DIR \
  --deposit-contract-address $ETH1_DEPOSIT_CONTRACT_ADDRESS \
  --min-genesis-active-validator-count $GENESIS_VALIDATOR_COUNT \
  --validator-count $VALIDATOR_COUNT \
  --min-genesis-time $GENESIS_TIME \
  --genesis-delay $GENESIS_DELAY \
  --genesis-fork-version $GENESIS_FORK_VERSION \
  --altair-fork-epoch $ALTAIR_FORK_EPOCH \
  --bellatrix-fork-epoch $BELLATRIX_FORK_EPOCH \
  --capella-fork-epoch $CAPELLA_FORK_EPOCH \
  --deneb-fork-epoch $DENEB_FORK_EPOCH \
  --eth1-id $ETH1_CHAIN_ID \
  --eth1-block-hash $ETH1_BLOCK_HASH \
  --eth1-follow-distance 1 \
  --seconds-per-slot $SECONDS_PER_SLOT \
  --seconds-per-eth1-block $SECONDS_PER_ETH1_BLOCK \
  --interop-genesis-state \
  --force

echo Specification and genesis.ssz generated at $TESTNET_DIR.
echo "Generating $VALIDATOR_COUNT validators concurrently... (this may take a while)"

lcli \
  insecure-validators \
  --count $VALIDATOR_COUNT \
  --base-dir $DATADIR \
  --node-count $BN_COUNT

echo Validators generated with keystore passwords at $DATADIR.
