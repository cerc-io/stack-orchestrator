import type { Config } from "@ponder/core";

import contractAddresses from "./nitro-addresses.json" assert { type: "json" };

export const config: Config = {
  networks: [
    {
      name: "fixturenet",
      chainId: Number(process.env.PONDER_CHAIN_ID),
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
    indexerGqlEndpoint: process.env.INDEXER_GQL_ENDPOINT,
  },
};
