import fs from 'fs'

import { task } from 'hardhat/config'
import '@nomiclabs/hardhat-ethers'

task('send-balance', 'Sends Ether to a specified Ethereum account')
  .addParam('to', 'The Ethereum address to send Ether to')
  .addParam('amount', 'The amount of Ether to send, in Ether')
  .addParam('privateKey', 'The private key of the sender')
  .setAction(async ({ to, amount, privateKey }, { ethers }) => {
    const fileContent = fs.readFileSync('/l2-accounts/keys.json', 'utf-8')
    const keySet = JSON.parse(fileContent)

    // Get the dest account address from the json file if key present
    let address: string = to
    if (to in keySet) {
      address = keySet[to].address
    }

    // Open the wallet using sender's private key
    const wallet = new ethers.Wallet(privateKey, ethers.provider)

    // Send amount to the specified address
    const tx = await wallet.sendTransaction({
      to: address,
      value: ethers.utils.parseEther(amount),
    })

    console.log(`Balance sent to: ${address}, from: ${wallet.address}`)
    console.log(`Transaction hash: ${tx.hash}`)
  })
