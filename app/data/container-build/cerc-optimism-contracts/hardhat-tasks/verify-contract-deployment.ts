import { task } from 'hardhat/config'
import '@nomiclabs/hardhat-ethers'

task(
  'verify-contract-deployment',
  'Verifies the given contract deployment transaction'
)
  .addParam('contract', 'Address of the contract deployed')
  .addParam('transactionHash', 'Hash of the deployment transaction')
  .setAction(async ({ contract, transactionHash }, { ethers }) => {
    const provider = new ethers.providers.JsonRpcProvider(
      `${process.env.L1_RPC}`
    )

    // Get the deployment tx receipt
    const receipt = await provider.getTransactionReceipt(transactionHash)
    if (
      receipt &&
      receipt.contractAddress &&
      receipt.contractAddress === contract
    ) {
      console.log(
        `Deployment for contract ${contract} in transaction ${transactionHash} verified`
      )
      process.exit(0)
    } else {
      console.log(`Contract ${contract} deployment verification failed`)
      process.exit(1)
    }
  })
