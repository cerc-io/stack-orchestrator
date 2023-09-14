import fs from 'fs';
import { providers, Wallet } from 'ethers';
import { deployContracts } from '@cerc-io/nitro-util';

async function main () {
  const rpcURL = process.env.RPC_URL;
  const addressesFilePath = process.env.NITRO_ADDRESSES_FILE_PATH;
  const deployerKey = process.env.PRIVATE_KEY;

  if (!rpcURL) {
    console.log('RPC_URL not set, skipping deployment');
    return;
  }

  if (!addressesFilePath) {
    console.log('NITRO_ADDRESSES_FILE_PATH not set, skipping deployment');
    return;
  }

  if (!deployerKey) {
    console.log('PRIVATE_KEY not set, skipping deployment');
    return;
  }

  const provider = new providers.JsonRpcProvider(process.env.RPC_URL);
  const signer = new Wallet(deployerKey, provider);

  const [
    nitroAdjudicatorAddress,
    virtualPaymentAppAddress,
    consensusAppAddress
  ] = await deployContracts(signer as any);

  const output = {
    nitroAdjudicatorAddress,
    virtualPaymentAppAddress,
    consensusAppAddress
  };

  fs.writeFileSync(addressesFilePath, JSON.stringify(output, null, 2));
  console.log('Nitro contracts deployed, addresses written to', addressesFilePath);
  console.log('Result:', JSON.stringify(output, null, 2));
}

main()
  .catch((err) => {
    console.log(err);
  });
