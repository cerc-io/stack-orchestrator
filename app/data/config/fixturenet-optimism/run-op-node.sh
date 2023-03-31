#!/bin/sh
set -e

# Get SEQUENCER KEY from keys.json
SEQUENCER_KEY=$(jq -r '.Sequencer.privateKey' /l2-accounts/keys.json | tr -d '"')

op-node \
	--l2=http://op-geth:8551 \
	--l2.jwt-secret=/app/jwt.txt \
	--sequencer.enabled \
	--sequencer.l1-confs=3 \
	--verifier.l1-confs=3 \
	--rollup.config=/app/rollup.json \
	--rpc.addr=0.0.0.0 \
	--rpc.port=8547 \
	--p2p.disable \
	--rpc.enable-admin \
	--p2p.sequencer.key=$SEQUENCER_KEY \
	--l1=$L1_RPC \
	--l1.rpckind=any
