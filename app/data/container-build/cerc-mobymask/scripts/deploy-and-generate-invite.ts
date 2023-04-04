import { ethers } from "ethers";
import fs from 'fs';
import path from 'path';

// Workaround for missing types
const { generateUtil } = require('eth-delegatable-utils');

const phisherRegistryArtifacts = require('../hardhat/artifacts/contracts/PhisherRegistry.sol/PhisherRegistry.json');
const { privateKey, rpcUrl, baseURI } = require('./secrets.json');


const DEFAULT_BASE_URI = 'https://mobymask.com/#';

const configPath = path.join(__dirname, './config.json');
const { abi } = phisherRegistryArtifacts;

let provider = new ethers.providers.JsonRpcProvider(rpcUrl);
let signer: ethers.Wallet;
let _chainId: string;
let _name: string = 'MobyMask';

setupSigner()
  .then(setupContract)
  .then(signDelegation)
  .catch(console.error);

async function setupSigner () {
  if (privateKey) {
    signer = new ethers.Wallet(privateKey, provider)
  }
}

async function setupContract (): Promise<ethers.Contract> {
  try {
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    const { address, chainId, name } = config;
    _name = name;
    _chainId = chainId;
    return attachToContract(address)
  } catch (err) {
    console.log('No config detected, deploying contract and creating one.');
    return deployContract()
  }
}

async function deployContract () {
  const Registry = new ethers.ContractFactory(abi, phisherRegistryArtifacts.bytecode, signer);
  const _name = 'MobyMask';
  const registry = await Registry.deploy(_name);

  const address = registry.address;
  fs.writeFileSync(configPath, JSON.stringify({ address, name: _name, chainId: registry.deployTransaction.chainId }, null, 2));
  try {
    return await registry.deployed();
  } catch (err) {
    console.log('Deployment failed, trying to attach to existing contract.', err);
    throw err;
  }
}

async function attachToContract(address: string) {
  const Registry = new ethers.Contract(address, abi, signer);
  const registry = await Registry.attach(address);
  console.log('Attaching to existing contract');
  const deployed = await registry.deployed();
  return deployed;
}

type Invocation = {
  transaction: Transaction,
  authority: SignedDelegation[],
};

type Transaction = {
  to: string,
  gasLimit: string,
  data: string,
};

type SignedDelegation = {
  delegation: Delegation,
  signature: string,
}

type Delegation = {
  delegate: string,
  authority: string,
  caveats: Caveat[],
};

type Caveat = {
  enforcer: string,
  terms: string,
}

type SignedInvocation = {
  invocation: Invocation,
  signature: string,
}

async function signDelegation (registry: ethers.Contract) {
  const { chainId } = await provider.getNetwork();
  const utilOpts = {
    chainId,
    verifyingContract: registry.address,
    name: _name,
  };
  console.log('util opts', utilOpts);
  const util = generateUtil(utilOpts)
  const delegate = ethers.Wallet.createRandom();

  // Prepare the delegation message.
  // This contract is also a revocation enforcer, so it can be used for caveats:
  const delegation = {
    delegate: delegate.address,
    authority: '0x0000000000000000000000000000000000000000000000000000000000000000',
    caveats: [{
      enforcer: registry.address,
      terms: '0x0000000000000000000000000000000000000000000000000000000000000000',
    }],
  };

  // Owner signs the delegation:
  const signedDelegation = util.signDelegation(delegation, signer.privateKey);
  const invitation = {
    v:1,
    signedDelegations: [signedDelegation],
    key: delegate.privateKey,
  }
  console.log('A SIGNED DELEGATION/INVITE LINK:');
  console.log(JSON.stringify(invitation, null, 2));
  console.log((baseURI ?? DEFAULT_BASE_URI) + '/members?invitation=' + encodeURIComponent(JSON.stringify(invitation)));
}
