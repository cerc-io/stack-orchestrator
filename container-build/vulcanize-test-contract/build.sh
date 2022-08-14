# Build vulcanize/test-contract
docker build -t vulcanize/test-contract:local --build-arg ETH_ADDR=http://go-ethereum:8545 ${VULCANIZE_REPO_BASE_DIR}/ipld-eth-db-validator/test/contract
