const { ethers } = require('ethers');
require('dotenv').config();

// EAS contract address on Base Sepolia
const EAS_CONTRACT_ADDRESS = '0xC2679fBD37d54388Ce493F1DB75320D236e1815e';

// Transaction options
const TX_OPTIONS = {
  gasLimit: 500000,
  gasPrice: ethers.utils.parseUnits('10', 'gwei')
};

// ABI for the EAS contract (just what we need for attestation)
const EAS_ABI = [
  "function attest(tuple(bytes32 schema, tuple(address recipient, uint64 expirationTime, bool revocable, bytes32 refUID, bytes data, uint256 value) data)) external payable returns (bytes32)"
];

// The schema that was just created in the UI
const SCHEMA_UID = "0x40aad7f118ba0f4f36c2036190fdc9df7b8bad9299744d5033ed843b1b00e0aa";

// New sample track with complete details
const newSampleTrack = {
  title: "Blockchain Beats",
  artist: "MESA Recording Artist",
  iswc: "T-987654321-0",
  publisher: "MESA Music Publishing"
};

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
    console.log("Creating new sample track attestation using the UI-created schema...");
    
    // Connect to Base Sepolia
    const provider = new ethers.providers.JsonRpcProvider("https://sepolia.base.org");
    
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
    
    // Create EAS contract instance
    const eas = new ethers.Contract(
      EAS_CONTRACT_ADDRESS,
      EAS_ABI,
      wallet
    );
    
    console.log(`Using existing schema with UID: ${SCHEMA_UID}`);
    
    // ABI encode the attestation data according to the schema structure
    const abiCoder = new ethers.utils.AbiCoder();
    const encodedData = abiCoder.encode(
      ["string", "string", "string", "address", "uint256", "string"],
      [
        newSampleTrack.title,
        newSampleTrack.artist,
        newSampleTrack.iswc,
        wallet.address, // rightsHolder
        123, // tokenId - just a sample value
        "ipfs://bafybeihbmin5hc6xqt553m6yqcwgmyto7skpxg2jwgivsb3plp7mxz7khm" // containerAddress - sample IPFS hash
      ]
    );
    
    // Create attestation data object
    const attestationData = {
      schema: SCHEMA_UID,
      data: {
        recipient: wallet.address, // Self-attestation for demonstration
        expirationTime: 0, // No expiration
        revocable: true,
        refUID: ethers.constants.HashZero,
        data: encodedData,
        value: 0
      }
    };
    
    console.log("Submitting attestation for new sample track...");
    console.log("Track details:");
    console.log(`  Title: ${newSampleTrack.title}`);
    console.log(`  Artist: ${newSampleTrack.artist}`);
    console.log(`  ISWC: ${newSampleTrack.iswc}`);
    console.log(`  Rights Holder: ${wallet.address}`);
    
    const attestTx = await eas.attest(attestationData, TX_OPTIONS);
    
    console.log(`Attestation transaction submitted: ${attestTx.hash}`);
    const attestReceipt = await waitForTransaction(attestTx);
    
    console.log("\n=== Sample Track Attestation Successful ===");
    console.log(`Transaction Hash (also Attestation UID): ${attestReceipt.transactionHash}`);
    console.log(`Block Number: ${attestReceipt.blockNumber}`);
    console.log(`Gas Used: ${attestReceipt.gasUsed.toString()}`);
    
    console.log("\nView your attestation on Base Sepolia EAS Explorer:");
    console.log(`https://base-sepolia.easscan.org/attestation/view/${attestReceipt.transactionHash}`);
    
    console.log("\nThis new attestation should be properly indexed and visible because:");
    console.log("1. We're using a schema UID that was created through the UI");
    console.log("2. The attestation data structure matches exactly what the schema expects");
    console.log("3. It will be properly associated with your wallet address as both attester and rights holder");
    
  } catch (error) {
    console.error("Error creating attestation:");
    console.error(error);
    process.exit(1);
  }
}

main(); 