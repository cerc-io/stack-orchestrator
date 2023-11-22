set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

echo "Using IPLD ETH RPC endpoint ${CERC_IPLD_ETH_RPC}"
echo "Using IPLD GQL endpoint ${CERC_IPLD_ETH_GQL}"

# Replace env variables in template TOML file
# Read in the config template TOML file and modify it
WATCHER_CONFIG_TEMPLATE=$(cat environments/watcher-config-template.toml)
WATCHER_CONFIG=$(echo "$WATCHER_CONFIG_TEMPLATE" | \
  sed -E "s|REPLACE_WITH_CERC_IPLD_ETH_RPC|${CERC_IPLD_ETH_RPC}|g; \
          s|REPLACE_WITH_CERC_IPLD_ETH_GQL|${CERC_IPLD_ETH_GQL}| ")

# Write the modified content to a new file
echo "$WATCHER_CONFIG" > environments/watcher-config.toml

# Merge SO watcher config with existing config file
node merge-toml.js

echo 'yarn job-runner'

yarn watch:contract --address 0x223c067F8CF28ae173EE5CafEa60cA44C335fecB --kind Azimuth --checkpoint true --starting-block 6784880
yarn yarn job-runner

