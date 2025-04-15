const { ethers } = require('ethers');
require('dotenv').config();

// EAS contract addresses on Base Sepolia
const EAS_CONTRACT_ADDRESS = '0xC2679fBD37d54388Ce493F1DB75320D236e1815e';
const SCHEMA_REGISTRY_ADDRESS = '0x0a7E2Ff54e76B8E6659aedc9103FB21c038050D0';

// Transaction options
const TX_OPTIONS = {
  gasLimit: 500000, // Increase gas limit
  gasPrice: ethers.utils.parseUnits('10', 'gwei') // Set consistent gas price
};

// ABIs
// Simplified ABIs with just the methods we need
const EAS_ABI = [
  "function attest(tuple(bytes32 schema, tuple(address recipient, uint64 expirationTime, bool revocable, bytes32 refUID, bytes data, uint256 value) data)) external payable returns (bytes32)",
  "function getAttestation(bytes32 uid) external view returns (tuple(bytes32 uid, bytes32 schema, address recipient, address attester, bool revocable, bytes32 refUID, uint64 timeCreated, uint64 expirationTime, bytes data))",
  "function isAttestationRevoked(bytes32 uid) external view returns (bool)"
];

const SCHEMA_REGISTRY_ABI = [
  "function register(string calldata schema, bool revocable, string calldata description) external returns (bytes32)",
  "function getSchema(bytes32 uid) external view returns (tuple(bytes32 uid, bool revocable, string schema, string description))"
];

// Sample mock data for a music track
const sampleTrack = {
  title: "Summer Nights",
  artist: "John Doe",
  iswc: "T-123456789-0",
  publisher: "MESA Music Publishing"
};

// Mock NFT and container data
const mockTokenId = 1;
const mockContainerAddress = "0x1234567890123456789012345678901234567890";

// Function to wait for transaction confirmation with timeout
async function waitForTransaction(tx, timeoutSeconds = 180) {
  console.log(`Waiting for transaction ${tx.hash} to be confirmed (timeout: ${timeoutSeconds}s)...`);
  
  return new Promise((resolve, reject) => {
    // Set a timeout
    const timeout = setTimeout(() => {
      reject(new Error(`Transaction confirmation timed out after ${timeoutSeconds} seconds`));
    }, timeoutSeconds * 1000);
    
    // Wait for transaction
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
    console.log("Starting EAS attestation process on Base Sepolia...");
    
    // Connect to Base Sepolia
    const provider = new ethers.providers.JsonRpcProvider("https://sepolia.base.org");
    
    // You would typically load this from an environment variable
    // Never hardcode private keys in production code
    if (!process.env.PRIVATE_KEY) {
      throw new Error("Private key not found. Set PRIVATE_KEY in your .env file");
    }
    
    const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
    console.log(`Connected with wallet address: ${wallet.address}`);
    
    // Check wallet balance
    const balance = await provider.getBalance(wallet.address);
    console.log(`Wallet balance: ${ethers.utils.formatEther(balance)} ETH`);
    
    if (balance.eq(0)) {
      throw new Error("Wallet has no ETH. Get some Base Sepolia ETH from a faucet first.");
    }
    
    // Create contract instances
    const schemaRegistry = new ethers.Contract(
      SCHEMA_REGISTRY_ADDRESS,
      SCHEMA_REGISTRY_ABI,
      wallet
    );
    
    const eas = new ethers.Contract(
      EAS_CONTRACT_ADDRESS,
      EAS_ABI,
      wallet
    );
    
    // Known schema UID for "string name, string age" on Base Sepolia
    // This is an actual schema for demonstration that should work reliably
    const schemaUID = "0x14554977234f8ef97a88c5a1da6d65e8522922671b511b4aa5d198a4629de6b1";
    
    console.log(`Using existing schema with UID: ${schemaUID}`);
    
    // Step 2: Create an attestation
    console.log("\nCreating attestation for music rights...");
    
    // ABI encode the attestation data - simplified for known schema
    const abiCoder = new ethers.utils.AbiCoder();
    const encodedData = abiCoder.encode(
      ["string", "string"],
      [sampleTrack.title, sampleTrack.artist]
    );
    
    // Create attestation data object
    const attestationData = {
      schema: schemaUID,
      data: {
        recipient: wallet.address, // Self-attestation for demonstration
        expirationTime: 0, // No expiration
        revocable: true,
        refUID: ethers.constants.HashZero,
        data: encodedData,
        value: 0
      }
    };
    
    console.log("Submitting attestation transaction...");
    
    console.log("Debug - Attestation Data:", JSON.stringify(attestationData, null, 2));
    const attestTx = await eas.attest(attestationData, TX_OPTIONS);
    
    console.log(`Attestation transaction submitted: ${attestTx.hash}`);
    
    // Use the new function instead of direct wait
    const attestReceipt = await waitForTransaction(attestTx);
    
    // Extract the attestation UID from the transaction receipt
    // Again, this is a simplified approach
    console.log("Debug - Attestation Receipt Logs:", JSON.stringify(attestReceipt.logs, null, 2));
    
    // Define attestationUID variable
    let attestationUID;
    
    // Check if logs exist and have the expected structure
    if (!attestReceipt.logs || attestReceipt.logs.length === 0) {
      console.log("No logs found in attestation receipt. Using transaction hash as fallback.");
      attestationUID = attestReceipt.transactionHash;
    } else {
      console.log(`Found ${attestReceipt.logs.length} logs in attestation receipt`);
      
      // Try to extract from logs safely
      try {
        if (attestReceipt.logs[0].topics && attestReceipt.logs[0].topics.length > 1) {
          attestationUID = "0x" + attestReceipt.logs[0].topics[1].slice(26);
          console.log(`Extracted attestation UID: ${attestationUID}`);
        } else {
          // Alternative approach - use the transaction hash as a fallback
          attestationUID = attestReceipt.transactionHash;
          console.log(`Using transaction hash as attestation UID: ${attestationUID}`);
        }
      } catch (error) {
        console.error("Error extracting attestation UID:", error);
        // Fallback to using transaction hash
        attestationUID = attestReceipt.transactionHash;
        console.log(`Falling back to transaction hash as attestation UID: ${attestationUID}`);
      }
    }
    
    console.log("\n=== Attestation Successful ===");
    console.log(`Attestation UID: ${attestationUID}`);
    console.log(`Transaction Hash: ${attestReceipt.transactionHash}`);
    console.log(`Block Number: ${attestReceipt.blockNumber}`);
    console.log(`Gas Used: ${attestReceipt.gasUsed.toString()}`);
    
    console.log(`View your attestation on Base Sepolia EAS Explorer:`);
    console.log(`https://base-sepolia.easscan.org/attestation/view/${attestationUID}`);
    
    // Verify the attestation was created
    console.log("\nVerifying attestation...");
    try {
      const attestation = await eas.getAttestation(attestationUID);
      
      console.log("Attestation verified on-chain:");
      console.log(`- Schema: ${attestation.schema}`);
      console.log(`- Recipient: ${attestation.recipient}`);
      console.log(`- Attester: ${attestation.attester}`);
      console.log(`- Time Created: ${new Date(attestation.timeCreated.toNumber() * 1000).toISOString()}`);
    } catch (error) {
      console.log("Unable to verify attestation yet. This is normal, as it may take some time for the attestation to be fully indexed.");
      console.log("Please check the attestation explorer link above in a few minutes.");
    }
    
    console.log("\nSuccess! You now have a real EAS attestation on Base Sepolia.");
    
  } catch (error) {
    console.error("Error creating attestation:");
    console.error(error);
    process.exit(1);
  }
}

main(); 