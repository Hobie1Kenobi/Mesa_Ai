const { ethers } = require('ethers');
require('dotenv').config();

// EAS contract addresses on Base Sepolia
const EAS_CONTRACT_ADDRESS = '0xC2679fBD37d54388Ce493F1DB75320D236e1815e';
const SCHEMA_REGISTRY_ADDRESS = '0x0a7E2Ff54e76B8E6659aedc9103FB21c038050D0';

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
    
    // Step 1: Register a schema for music rights
    console.log("Registering schema...");
    
    // Define the schema string - must match the format expected by EAS
    const schemaString = "tuple(string title, string artist, string iswc, address rightsHolder, uint256 tokenId, string containerAddress)";
    
    // Register the schema
    // Note: Check if you already have a schema registered to avoid duplicates
    console.log("Submitting schema registration transaction...");
    const schemaTx = await schemaRegistry.register(
      schemaString,
      true, // revocable
      "Music Rights Registration Attestation Schema"
    );
    
    console.log(`Schema registration transaction submitted: ${schemaTx.hash}`);
    console.log("Waiting for confirmation...");
    
    const schemaReceipt = await schemaTx.wait();
    
    // Find the schema UID from the transaction events
    // This assumes the schema registry emits an event with the UID
    // Actual event parsing depends on the contract implementation
    
    // For demo purposes, we'll extract it from the logs
    // In a real implementation, you'd need to know the exact event signature and parse appropriately
    console.log("Transaction confirmed!");
    console.log("Looking for schema UID in logs...");
    
    // This is a simplified approach - in reality, you'd need to parse the event properly
    const schemaUID = "0x" + schemaReceipt.logs[0].topics[1].slice(26);
    console.log(`Schema registered with UID: ${schemaUID}`);
    
    // Step 2: Create an attestation
    console.log("\nCreating attestation for music rights...");
    
    // ABI encode the attestation data according to the schema
    const abiCoder = new ethers.utils.AbiCoder();
    const encodedData = abiCoder.encode(
      ["tuple(string title, string artist, string iswc, address rightsHolder, uint256 tokenId, string containerAddress)"],
      [{
        title: sampleTrack.title,
        artist: sampleTrack.artist,
        iswc: sampleTrack.iswc,
        rightsHolder: wallet.address,
        tokenId: mockTokenId,
        containerAddress: mockContainerAddress
      }]
    );
    
    // Create attestation data object
    const attestationData = {
      schema: schemaUID,
      data: {
        recipient: mockContainerAddress,
        expirationTime: 0, // No expiration
        revocable: true,
        refUID: ethers.constants.HashZero,
        data: encodedData,
        value: 0
      }
    };
    
    console.log("Submitting attestation transaction...");
    const attestTx = await eas.attest(attestationData);
    
    console.log(`Attestation transaction submitted: ${attestTx.hash}`);
    console.log("Waiting for confirmation...");
    
    const attestReceipt = await attestTx.wait();
    
    // Extract the attestation UID from the transaction receipt
    // Again, this is a simplified approach
    const attestationUID = "0x" + attestReceipt.logs[0].topics[1].slice(26);
    
    console.log("\n=== Attestation Successful ===");
    console.log(`Attestation UID: ${attestationUID}`);
    console.log(`Transaction Hash: ${attestReceipt.transactionHash}`);
    console.log(`Block Number: ${attestReceipt.blockNumber}`);
    console.log(`Gas Used: ${attestReceipt.gasUsed.toString()}`);
    
    console.log("\nView your attestation on Base Sepolia EAS Explorer:");
    console.log(`https://base-sepolia.easscan.org/attestation/view/${attestationUID}`);
    
    // Verify the attestation was created
    console.log("\nVerifying attestation...");
    const attestation = await eas.getAttestation(attestationUID);
    
    console.log("Attestation verified on-chain:");
    console.log(`- Schema: ${attestation.schema}`);
    console.log(`- Recipient: ${attestation.recipient}`);
    console.log(`- Attester: ${attestation.attester}`);
    console.log(`- Time Created: ${new Date(attestation.timeCreated.toNumber() * 1000).toISOString()}`);
    
    console.log("\nSuccess! You now have a real EAS attestation on Base Sepolia.");
    
  } catch (error) {
    console.error("Error creating attestation:");
    console.error(error);
    process.exit(1);
  }
}

main(); 