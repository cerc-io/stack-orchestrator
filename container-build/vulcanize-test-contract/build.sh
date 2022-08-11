# Build vulcanize/test-contract
docker build -t vulcanize/test-contract:local ${vulcanize_repo_base_dir}/ipld-eth-db-validator/test/contract

#version: "3.2"
#services:
#  contract:
#    depends_on:
#      go-ethereum:
#        condition: service_healthy
#    build:
#      context: ${vulcanize_test_contract}
#      args:
#        ETH_ADDR: "http://go-ethereum:8545"
#    environment:
#      ETH_ADDR: "http://go-ethereum:8545"
#    ports:
#      - "127.0.0.1:3000:3000"