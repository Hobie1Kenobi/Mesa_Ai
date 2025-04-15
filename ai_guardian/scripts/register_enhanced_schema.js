const { ethers } = require('ethers');
require('dotenv').config();

// EAS contract addresses on Base Sepolia
const SCHEMA_REGISTRY_ADDRESS = '0x0a7E2Ff54e76B8E6659aedc9103FB21c038050D0';
const EAS_CONTRACT_ADDRESS = '0xC2679fBD37d54388Ce493F1DB75320D236e1815e';

// ABI for schema registry (minimal)
const SCHEMA_REGISTRY_ABI = [
  "function register(string calldata schema, address resolver, bool revocable) external returns (bytes32)",
  "event Registered(bytes32 indexed uid, address indexed registerer, bytes32 indexed schema, string schemaData, address resolver, bool revocable)"
];

// Transaction options
const TX_OPTIONS = {
  gasLimit: 1000000,
  gasPrice: ethers.utils.parseUnits('10', 'gwei')
};

// Function to wait for transaction confirmation
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
    console.log("Registering enhanced music rights schema...");
    
    // Connect to Base Sepolia
    const provider = new ethers.providers.JsonRpcProvider(process.env.BASE_SEPOLIA_RPC_URL || "https://sepolia.base.org");
    
    if (!process.env.PRIVATE_KEY) {
      throw new Error("Private key not found. Set PRIVATE_KEY in your .env file");
    }
    
    const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
    console.log(`Connected with wallet address: ${wallet.address}`);
    
    const balance = await provider.getBalance(wallet.address);
    console.log(`Wallet balance: ${ethers.utils.formatEther(balance)} ETH`);
    
    if (balance.eq(0)) {
      throw new Error("Wallet has no ETH. Get some Base Sepolia ETH from a faucet first.");
    }
    
    // Create Schema Registry contract instance
    const schemaRegistry = new ethers.Contract(
      SCHEMA_REGISTRY_ADDRESS,
      SCHEMA_REGISTRY_ABI,
      wallet
    );
    
    // Define the enhanced schema with all requested fields
    const schema = "string track_title, string artist_name, string publisher, " +
      "string rights_type, string jurisdiction, " +
      "string rightsholder_name, string rightsholder_email, string rightsholder_role, " +
      "string rightsholder_ipi, string split_percentage, string rightsholder_address, " +
      "string rightsholder_phone, string rightsholder_id, " +
      "string iswc_code, string isrc_code, string designated_administrator, " +
      "address wallet_address, string mesa_verified";
    
    console.log("\nRegistering schema with the following structure:");
    console.log(schema);
    
    // No resolver for now
    const resolverAddress = "0x0000000000000000000000000000000000000000";
    const revocable = true;
    
    // Register the schema
    console.log("\nSubmitting schema registration...");
    const tx = await schemaRegistry.register(
      schema,
      resolverAddress,
      revocable,
      TX_OPTIONS
    );
    
    console.log(`Schema registration transaction submitted: ${tx.hash}`);
    const receipt = await waitForTransaction(tx);
    
    // Extract schema UID from logs - fix the extraction method
    let schemaUID;
    
    // Find the Registered event in the logs and extract the UID
    for (const log of receipt.logs) {
      try {
        // Try to parse the log as a Registered event
        const parsedLog = schemaRegistry.interface.parseLog(log);
        if (parsedLog.name === 'Registered') {
          schemaUID = parsedLog.args.uid;
          break;
        }
      } catch (error) {
        // Skip logs that are not from our contract/event
        continue;
      }
    }
    
    // If we couldn't find the UID in the logs, try to use the transaction hash as fallback
    if (!schemaUID) {
      console.warn("Couldn't extract schema UID from logs, using transaction hash as fallback");
      schemaUID = receipt.transactionHash;
    }
    
    console.log("\n=== Schema Registration Successful ===");
    console.log(`Schema UID: ${schemaUID}`);
    console.log(`Transaction Hash: ${receipt.transactionHash}`);
    console.log(`Block Number: ${receipt.blockNumber}`);
    console.log(`Gas Used: ${receipt.gasUsed.toString()}`);
    
    console.log("\nView your schema on Base Sepolia EAS Explorer:");
    console.log(`https://base-sepolia.easscan.org/schema/view/${schemaUID}`);
    
    console.log("\nAdd the following to your .env file:");
    console.log(`ENHANCED_SCHEMA_UID=${schemaUID}`);
    
    // Update .env file or create a configuration
    console.log("\nSaving schema UID to schema_config.json...");
    const fs = require('fs');
    fs.writeFileSync(
      './schema_config.json', 
      JSON.stringify({ schemaUID, timestamp: new Date().toISOString() }, null, 2)
    );
    console.log("Configuration saved!");
    
    return schemaUID;
    
  } catch (error) {
    console.error("Error registering schema:");
    console.error(error);
    process.exit(1);
  }
}

main(); 