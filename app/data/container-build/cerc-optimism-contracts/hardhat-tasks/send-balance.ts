import { task } from 'hardhat/config'
import '@nomiclabs/hardhat-ethers'
import { ethers } from 'ethers'

task('send-balance', 'Sends Ether to a specified Ethereum account')
  .addParam('to', 'The Ethereum address to send Ether to')
  .addParam('amount', 'The amount of Ether to send, in Ether')
  .addParam('privateKey', 'The private key of the sender')
  .setAction(async ({ to, amount, privateKey }, {}) => {
    // Open the wallet using sender's private key
    const provider = new ethers.providers.JsonRpcProvider(`${process.env.CERC_L1_RPC}`)
    const wallet = new ethers.Wallet(privateKey, provider)

    // Send amount to the specified address
    const tx = await wallet.sendTransaction({
      to,
      value: ethers.utils.parseEther(amount),
    })
    const txReceipt = await tx.wait()

    console.log(`Balance sent to: ${to}, from: ${wallet.address}`)
    console.log(
      `Block: { number: ${txReceipt.blockNumber}, hash: ${txReceipt.blockHash} }`
    )
    console.log(`Transaction hash: ${tx.hash}`)
  })
