import type { Config } from "@ponder/core";

import contractAddresses from "./nitro-addresses.json";

export const config: Config = {
  networks: [
    {
      name: "fixturenet",
      chainId: Number(process.env.PONDER_CHAIN_ID),
      rpcUrl: process.env.PONDER_RPC_URL_1,
      maxRpcRequestConcurrency: 1,
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
    privateKey: process.env.CERC_PONDER_NITRO_PK!,
    chainPrivateKey: process.env.CERC_PONDER_NITRO_CHAIN_PK!,
    chainURL: process.env.CERC_PONDER_NITRO_CHAIN_URL!,
    contractAddresses,
    relayMultiAddr: process.env.CERC_RELAY_MULTIADDR!,
    store: "./.ponder/nitro-db",
    rpcNitroNode: {
      address: process.env.CERC_UPSTREAM_NITRO_ADDRESS!,
      multiAddr: process.env.CERC_UPSTREAM_NITRO_MULTIADDR!,
    },
    payAmount: process.env.CERC_UPSTREAM_NITRO_PAY_AMOUNT!,
  },
};
