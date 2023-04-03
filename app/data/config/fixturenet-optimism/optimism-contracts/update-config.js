const fs = require('fs')

// Get the command-line argument
const configFile = process.argv[2]
const adminAddress = process.argv[3]
const proposerAddress = process.argv[4]
const batcherAddress = process.argv[5]
const sequencerAddress = process.argv[6]
const blockHash = process.argv[7]

// Read the JSON file
const configData = fs.readFileSync(configFile)
const configObj = JSON.parse(configData)

// Update the finalSystemOwner property with the ADMIN_ADDRESS value
configObj.finalSystemOwner =
  configObj.portalGuardian =
  configObj.controller =
  configObj.l2OutputOracleChallenger =
  configObj.proxyAdminOwner =
  configObj.baseFeeVaultRecipient =
  configObj.l1FeeVaultRecipient =
  configObj.sequencerFeeVaultRecipient =
  configObj.governanceTokenOwner =
    adminAddress

configObj.l2OutputOracleProposer = proposerAddress

configObj.batchSenderAddress = batcherAddress

configObj.p2pSequencerAddress = sequencerAddress

configObj.l1StartingBlockTag = blockHash

// Write the updated JSON object back to the file
fs.writeFileSync(configFile, JSON.stringify(configObj, null, 2))
