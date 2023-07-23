import fs from 'fs'

import { task } from 'hardhat/config'
import { hdkey } from 'ethereumjs-wallet'
import * as bip39 from 'bip39'

task('rekey-json', 'Generates a new set of keys for a test network')
  .addParam('output', 'JSON file to output accounts to')
  .setAction(async ({ output: outputFile }) => {
    const mnemonic = bip39.generateMnemonic()
    const pathPrefix = "m/44'/60'/0'/0"
    const labels = ['Admin', 'Proposer', 'Batcher', 'Sequencer']
    const hdwallet = hdkey.fromMasterSeed(await bip39.mnemonicToSeed(mnemonic))

    const output = {}

    for (let i = 0; i < labels.length; i++) {
      const label = labels[i]
      const wallet = hdwallet.derivePath(`${pathPrefix}/${i}`).getWallet()
      const addr = '0x' + wallet.getAddress().toString('hex')
      const pk = wallet.getPrivateKey().toString('hex')

      output[label] = { address: addr, privateKey: pk }
    }

    fs.writeFileSync(outputFile, JSON.stringify(output, null, 2))
    console.log(`L2 account keys written to ${outputFile}`)
  })
