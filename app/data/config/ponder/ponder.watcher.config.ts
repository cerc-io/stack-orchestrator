import { type Config, AppMode } from "@ponder/core";

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
      address: process.env.ERC20_CONTRACT,
      startBlock: 5,
      maxBlockRange: 100,
    },
  ],
  options: {
    mode: AppMode.Watcher,
  },
  indexer: {
    gqlEndpoint: process.env.INDEXER_GQL_ENDPOINT,
    payments: {
      nitro: {
        address: process.env.INDEXER_NITRO_ADDRESS,
        fundingAmounts: {
          directFund: "1000000000000",
          virtualFund: "1000000000",
        },
      },
      amount: process.env.INDEXER_NITRO_PAY_AMOUNT,
    },
  },
  nitro: {
    privateKey: process.env.PONDER_NITRO_PK!,
    chainPrivateKey: process.env.PONDER_NITRO_CHAIN_PK!,
    chainUrl: process.env.PONDER_NITRO_CHAIN_URL!,
    contractAddresses,
    relayMultiAddr: process.env.RELAY_MULTIADDR!,
    store: "./.ponder/nitro-db",
    payments: {
      cache: {
        maxAccounts: 1000,
        accountTTLInSecs: 1800,
        maxVouchersPerAccount: 1000,
        voucherTTLInSecs: 300,
        maxPaymentChannels: 10000,
        paymentChannelTTLInSecs: 1800,
      },
      ratesFile: "./base-rates-config.json",
      requestTimeoutInSecs: 10,
    },
  }
};
