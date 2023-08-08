# SushiSwap Watcher Smoke Tests

## sushi-watcher

Deploy required contracts and set the addresses to variables:

```bash
# Deploy UniswapV3Factory
docker exec -it sushiswap-sushiswap-v3-core-1 pnpm hardhat --network docker deploy --tags UniswapV3Factory

# Set the returned address to a variable
export FACTORY_ADDRESS=<FACTORY_ADDRESS>

# Deploy TestUniswapV3Callee
docker exec -it sushiswap-sushiswap-v3-core-1 pnpm hardhat --network docker deploy --tags TestUniswapV3Callee

# Set the returned address to a variable
export UNISWAP_CALLEE_ADDRESS=<UNISWAP_CALLEE_ADDRESS>

# Deploy NFPM contract
docker exec -it sushiswap-sushiswap-v3-periphery-1 bash -c "export FACTORY_ADDRESS=$FACTORY_ADDRESS && yarn hardhat --network docker deploy --tags NonfungiblePositionManager"

# Set the returned address to a variable
export POSITION_MANAGER_ADDRESS=<POSITION_MANAGER_ADDRESS>

# Deploy two test tokens
docker exec -it sushiswap-sushiswap-v3-periphery-1 yarn hardhat --network docker deploy --tags TestERC20
docker exec -it sushiswap-sushiswap-v3-periphery-1 yarn hardhat --network docker deploy --tags TestERC20

# Set the returned addresses to variables
export TOKEN0_ADDRESS=<TOKEN0_ADDRESS>
export TOKEN1_ADDRESS=<TOKEN1_ADDRESS>
```

Watch the contracts:

```bash
# Watch factory contract
docker exec -it sushiswap-sushiswap-watcher-server-1 bash -c "yarn watch:contract --address $FACTORY_ADDRESS --kind factory --startingBlock 100 --checkpoint false"
docker exec -it sushiswap-sushiswap-info-watcher-server-1 bash -c "yarn watch:contract --address $FACTORY_ADDRESS --kind factory --startingBlock 100 --checkpoint false"

# Watch NFPM contract
docker exec -it sushiswap-sushiswap-watcher-server-1 bash -c "yarn watch:contract --address $POSITION_MANAGER_ADDRESS --kind nfpm --startingBlock 100 --checkpoint false"
docker exec -it sushiswap-sushiswap-info-watcher-server-1 bash -c "yarn watch:contract --address $POSITION_MANAGER_ADDRESS --kind nfpm --startingBlock 100 --checkpoint false"
```

Run the smoke test:

```bash
docker exec -it sushiswap-sushiswap-watcher-server-1 bash -c "export TOKEN0_ADDRESS=$TOKEN0_ADDRESS && export TOKEN1_ADDRESS=$TOKEN1_ADDRESS && export UNISWAP_CALLEE_ADDRESS=$UNISWAP_CALLEE_ADDRESS && yarn smoke-test"
```

## sushi-info-watcher

Deploy required contracts and set the addresses to variables:

```bash
# Deploy TestUniswapV3Callee
docker exec -it sushiswap-sushiswap-v3-core-1 pnpm hardhat --network docker deploy --tags TestUniswapV3Callee

# Set the returned address to a variable
export UNISWAP_CALLEE_ADDRESS=<UNISWAP_CALLEE_ADDRESS>

# Deploy two test tokens
docker exec -it sushiswap-sushiswap-v3-periphery-1 yarn hardhat --network docker deploy --tags TestERC20
docker exec -it sushiswap-sushiswap-v3-periphery-1 yarn hardhat --network docker deploy --tags TestERC20

# Set the returned addresses to variables
export TOKEN0_ADDRESS=<TOKEN0_ADDRESS>
export TOKEN1_ADDRESS=<TOKEN1_ADDRESS>
```

Run the smoke test:

```bash
docker exec -it sushiswap-sushiswap-info-watcher-server-1 bash -c "export TOKEN0_ADDRESS=$TOKEN0_ADDRESS && export TOKEN1_ADDRESS=$TOKEN1_ADDRESS && export UNISWAP_CALLEE_ADDRESS=$UNISWAP_CALLEE_ADDRESS && yarn smoke-test"
```
