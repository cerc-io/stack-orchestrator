module.exports = {
  network: 'filecoin',
  v3: {
    factory: {
      // https://filfox.info/en/address/0xc35DADB65012eC5796536bD9864eD8773aBc74C4
      address: '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
      startBlock: 2867560,
    },
    positionManager: {
      // https://filfox.info/en/address/0xF4d73326C13a4Fc5FD7A064217e12780e9Bd62c3
      address: '0xF4d73326C13a4Fc5FD7A064217e12780e9Bd62c3',
      startBlock: 2868037
    },
    // https://filfox.info/en/address/0x60E1773636CF5E4A227d9AC24F20fEca034ee25A
    native: { address: '0x60E1773636CF5E4A227d9AC24F20fEca034ee25A' },
    whitelistedTokenAddresses: [
      '0x60E1773636CF5E4A227d9AC24F20fEca034ee25A',
    ],
    stableTokenAddresses: [
    ],
    // TODO: Check value
    minimumEthLocked: 1.5
  }
}
