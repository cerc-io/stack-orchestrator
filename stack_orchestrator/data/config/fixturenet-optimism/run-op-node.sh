#!/bin/sh
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

CERC_L1_CHAIN_ID="${CERC_L1_CHAIN_ID:-${DEFAULT_CERC_L1_CHAIN_ID}}"
CERC_L1_RPC="${CERC_L1_RPC:-${DEFAULT_CERC_L1_RPC}}"
DEPLOYMENT_CONTEXT="$CERC_L1_CHAIN_ID"

deploy_config_file="/l2-config/$DEPLOYMENT_CONTEXT.json"
deployment_dir="/l1-deployment/$DEPLOYMENT_CONTEXT"
genesis_outfile="/l2-config/genesis.json"
rollup_outfile="/l2-config/rollup.json"

# Generate L2 genesis (if not already done)
if [ ! -f "$genesis_outfile" ] || [ ! -f "$rollup_outfile" ]; then
	op-node genesis l2 \
		--deploy-config $deploy_config_file \
		--deployment-dir $deployment_dir \
		--outfile.l2 $genesis_outfile \
		--outfile.rollup $rollup_outfile \
		--l1-rpc $CERC_L1_RPC
fi

# Start op-node
SEQ_KEY=$(cat /l2-accounts/accounts.json | jq -r .SeqKey)
jwt_file=/l2-config/l2-jwt.txt
L2_AUTH="http://op-geth:8551"
RPC_KIND=any # this can optionally be set to a preset for common node providers like Infura, Alchemy, etc.

op-node \
	--l2=$L2_AUTH \
	--l2.jwt-secret=$jwt_file \
	--sequencer.enabled \
	--sequencer.l1-confs=5 \
	--verifier.l1-confs=4 \
	--rollup.config=$rollup_outfile \
	--rpc.addr=0.0.0.0 \
	--rpc.port=8547 \
	--p2p.disable \
	--rpc.enable-admin \
	--p2p.sequencer.key="${SEQ_KEY#0x}" \
	--l1=$CERC_L1_RPC \
	--l1.rpckind=$RPC_KIND
