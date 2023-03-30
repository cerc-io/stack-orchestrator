import { task } from 'hardhat/config'
import '@nomiclabs/hardhat-ethers'

task('send-balance', 'Sends Ether to a specified Ethereum account')
  .addParam('to', 'The Ethereum address to send Ether to')
  .addParam('amount', 'The amount of Ether to send, in Ether')
  .addParam('privateKey', 'The private key of the sender')
  .setAction(async ({ to, amount, privateKey }, { ethers }) => {
    // Open the wallet using sender's private key
    const wallet = new ethers.Wallet(privateKey, ethers.provider)

    // Send amount to the specified address
    const tx = await wallet.sendTransaction({
      to,
      value: ethers.utils.parseEther(amount),
    })

    console.log(`Balance sent to: ${to}, from: ${wallet.address}`)
    console.log(`Transaction hash: ${tx.hash}`)
  })
