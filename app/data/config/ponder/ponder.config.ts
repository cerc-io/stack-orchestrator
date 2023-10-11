import type { Config } from "@ponder/core";

import contractAddresses from "./nitro-addresses.json" assert { type: "json" };

export const config: Config = {
  networks: [
    {
      name: "fixturenet",
      chainId: Number(process.env.PONDER_CHAIN_ID),
      rpcUrl: process.env.PONDER_RPC_URL_1,
      maxRpcRequestConcurrency: 1,
      pollingInterval: 5000,
      payments: {
        nitro: {
          address: process.env.UPSTREAM_NITRO_ADDRESS!,
          multiAddr: process.env.UPSTREAM_NITRO_MULTIADDR!,
          fundingAmounts: {
            // TODO: Pass amounts from env
            directFund: "1000000000000",
            virtualFund: "1000000000",
          },
        },
        paidRPCMethods: [
          "eth_getLogs",
          "eth_getBlockByNumber",
          "eth_getBlockByHash",
        ],
        amount: process.env.UPSTREAM_NITRO_PAY_AMOUNT!,
      },
    },
  ],
  contracts: [
    {
      name: "AdventureGold",
      network: "fixturenet",
      abi: "./abis/AdventureGold.json",
      address: "0x32353A6C91143bfd6C7d363B546e62a9A2489A20",
      startBlock: 5,
      maxBlockRange: 100,
    },
  ],
  nitro: {
    privateKey: process.env.PONDER_NITRO_PK!,
    chainPrivateKey: process.env.PONDER_NITRO_CHAIN_PK!,
    chainUrl: process.env.PONDER_NITRO_CHAIN_URL!,
    contractAddresses,
    relayMultiAddr: process.env.RELAY_MULTIADDR!,
    store: "./.ponder/nitro-db",
  },
  options: {
    /** GQL endpoint of the indexer, required when running app in watcher mode */
    indexerGqlEndpoint: "http://ponder-app-indexer:42070/graphql"
  }
};
