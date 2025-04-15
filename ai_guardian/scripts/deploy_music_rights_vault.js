const { ethers } = require('ethers');
require('dotenv').config();
const fs = require('fs');

// Deployment configuration
const TX_OPTIONS = {
  gasLimit: 4000000,
  gasPrice: ethers.utils.parseUnits('10', 'gwei')
};

// Load the compiled contract data
const contractJsonPath = '../out/MusicRightsVault.sol/MusicRightsVault.json';
let contractData;
try {
  contractData = JSON.parse(fs.readFileSync(contractJsonPath, 'utf8'));
} catch (error) {
  console.error(`Error reading contract file at ${contractJsonPath}: ${error.message}`);
  process.exit(1);
}

// Extract ABI and bytecode from the loaded file
const MUSIC_RIGHTS_VAULT_ABI = contractData.abi;
const BYTECODE = contractData.bytecode.object;

// Function to wait for transaction confirmation with timeout
async function waitForTransaction(tx, timeoutSeconds = 180) {
  console.log(`Waiting for transaction ${tx.hash} to be confirmed (timeout: ${timeoutSeconds}s)...`);
  
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error(`Transaction confirmation timed out after ${timeoutSeconds} seconds`));
    }, timeoutSeconds * 1000);
    
    tx.wait()
      .then((receipt) => {
        clearTimeout(timeout);
        console.log(`Transaction confirmed in block ${receipt.blockNumber}`);
        resolve(receipt);
      })
      .catch((error) => {
        clearTimeout(timeout);
        reject(error);
      });
  });
}

async function main() {
  try {
    console.log("Starting MusicRightsVault deployment on Base Sepolia...");
    
    // Connect to Base Sepolia
    const provider = new ethers.providers.JsonRpcProvider("https://sepolia.base.org");
    
    if (!process.env.PRIVATE_KEY) {
      throw new Error("Private key not found. Set PRIVATE_KEY in your .env file");
    }
    
    const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
    console.log(`Deployer address: ${wallet.address}`);
    
    const balance = await provider.getBalance(wallet.address);
    console.log(`Wallet balance: ${ethers.utils.formatEther(balance)} ETH`);
    
    if (balance.eq(0)) {
      throw new Error("Wallet has no ETH. Get some Base Sepolia ETH from a faucet first.");
    }

    // Check if we have enough balance to deploy (rough estimate)
    const estimatedCost = ethers.utils.parseEther("0.01"); // Estimate 0.01 ETH for deployment
    if (balance.lt(estimatedCost)) {
      throw new Error(`Insufficient balance. Need approximately ${ethers.utils.formatEther(estimatedCost)} ETH for deployment.`);
    }
    
    // Create contract factory
    const MusicRightsVaultFactory = new ethers.ContractFactory(
      MUSIC_RIGHTS_VAULT_ABI,
      BYTECODE,
      wallet
    );
    
    console.log("Deploying MusicRightsVault contract...");
    const deployTx = await MusicRightsVaultFactory.deploy(TX_OPTIONS);
    
    console.log(`Deployment transaction submitted: ${deployTx.deployTransaction.hash}`);
    console.log("Waiting for deployment confirmation...");
    
    // Wait for the contract to be deployed
    const musicRightsVault = await deployTx.deployed();
    
    console.log("\n=== MusicRightsVault Deployment Successful ===");
    console.log(`Contract Address: ${musicRightsVault.address}`);
    console.log(`Transaction Hash: ${deployTx.deployTransaction.hash}`);
    console.log(`Gas Used: ${(await deployTx.deployTransaction.wait()).gasUsed.toString()}`);
    
    console.log("\nView your contract on Base Sepolia Explorer:");
    console.log(`https://sepolia.basescan.org/address/${musicRightsVault.address}`);
    
    // Save contract address to a file for easy access by other scripts
    fs.writeFileSync('deployed_contract_address.txt', musicRightsVault.address);
    console.log("Contract address saved to deployed_contract_address.txt");
    
    // Update the integration script with the new contract address
    try {
      const integrationScriptPath = './integrate_attestations_with_vault.js';
      let integrationScript = fs.readFileSync(integrationScriptPath, 'utf8');
      
      // Replace placeholder contract address with the real one
      integrationScript = integrationScript.replace(
        /MUSIC_RIGHTS_VAULT_ADDRESS = '0x... your contract address ...'/,
        `MUSIC_RIGHTS_VAULT_ADDRESS = '${musicRightsVault.address}'`
      );
      
      fs.writeFileSync(integrationScriptPath, integrationScript);
      console.log(`Updated integration script with contract address: ${integrationScriptPath}`);
    } catch (error) {
      console.warn(`Could not update integration script: ${error.message}`);
    }
    
    // Update the deployed_contracts.json file
    try {
      const deployedContractsPath = './deployed_contracts.json';
      let deployedContracts = {};
      
      // Try to read existing file
      try {
        deployedContracts = JSON.parse(fs.readFileSync(deployedContractsPath, 'utf8'));
      } catch (error) {
        // If file doesn't exist or is invalid, create a new object
        console.log("Creating new deployed_contracts.json file");
      }
      
      // Add or update the MusicRightsVault entry
      deployedContracts.MusicRightsVault = musicRightsVault.address;
      
      // Write the updated contracts back to the file
      fs.writeFileSync(deployedContractsPath, JSON.stringify(deployedContracts, null, 2));
      console.log(`Updated deployed contracts file: ${deployedContractsPath}`);
    } catch (error) {
      console.warn(`Could not update deployed contracts file: ${error.message}`);
    }
    
    console.log("\nNext steps:");
    console.log("1. Create an attestation using create_sample_attestation.js");
    console.log("2. Run the integration script: node integrate_attestations_with_vault.js <attestation_uid>");
    
  } catch (error) {
    console.error("Error deploying contract:");
    console.error(error);
    process.exit(1);
  }
}

// Execute main function
main(); 