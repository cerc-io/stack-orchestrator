# Build cerc/test-contract
docker build -t cerc/test-contract:local --build-arg ETH_ADDR=http://go-ethereum:8545 ${CERC_REPO_BASE_DIR}/ipld-eth-db-validator/test/contract
