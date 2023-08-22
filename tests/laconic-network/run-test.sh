#!/bin/bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

node_count=4
node_dir_prefix="laconic-network-dir"
chain_id="laconic_81337-6"
node_moniker_prefix="node"

echo "Deleting any existing network directories..."
for (( i=1 ; i<=$node_count ; i++ )); 
do
    node_network_dir=${node_dir_prefix}${i}
    if [[ -d $node_network_dir ]]; then
        echo "Deleting ${node_network_dir}"
        rm -rf ${node_network_dir}
    fi
done

echo "Initalizing ${node_count} nodes networks..."
for (( i=1 ; i<=$node_count ; i++ )); 
do
    node_network_dir=${node_dir_prefix}${i}
    node_moniker=${node_moniker_prefix}${i}
    laconic-so --stack mainnet-laconic deploy setup --network-dir ${node_network_dir} --initialize-network --chain-id ${chain_id} --node-moniker ${node_moniker}
done

echo "Joining ${node_count} nodes to the network..."
for (( i=1 ; i<=$node_count ; i++ )); 
do
    node_network_dir=${node_dir_prefix}${i}
    node_moniker=${node_moniker_prefix}${i}
    laconic-so --stack mainnet-laconic deploy setup --network-dir ${node_network_dir} --join-network --key-name ${node_moniker}
done

echo "Merging ${node_count} nodes genesis txns..."
gentx_files=""
delimeter=""
# Note: start at node 2 here because we're going to copy to node 1
for (( i=2 ; i<=$node_count ; i++ ));
do
    node_network_dir=${node_dir_prefix}${i}
    node_gentx_file=$(ls ${node_network_dir}/config/gentx/*.json)
    gentx_files+=${delimeter}${node_gentx_file}
    delimeter=","
done
laconic-so --stack mainnet-laconic deploy setup --network-dir ${node_dir_prefix}1 --create-network --gentx-files ${gentx_files}
