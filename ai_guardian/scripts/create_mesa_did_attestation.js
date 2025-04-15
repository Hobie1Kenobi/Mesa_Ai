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
const EAS_ABI = [
  "function attest(tuple(bytes32 schema, tuple(address recipient, uint64 expirationTime, bool revocable, bytes32 refUID, bytes data, uint256 value) data)) external payable returns (bytes32)",
  "function getAttestation(bytes32 uid) external view returns (tuple(bytes32 uid, bytes32 schema, address recipient, address attester, bool revocable, bytes32 refUID, uint64 timeCreated, uint64 expirationTime, bytes data))",
  "function isAttestationRevoked(bytes32 uid) external view returns (bool)"
];

const SCHEMA_REGISTRY_ABI = [
  "function register(string calldata schema, bool revocable, string calldata description) external returns (bytes32)",
  "function getSchema(bytes32 uid) external view returns (tuple(bytes32 uid, bool revocable, string schema, string description))"
];

// MESA AI brand information
const mesaInfo = {
  name: "MESA",
  description: "Protecting music rights with professional splits contracts and work-for-hire agreements, ensuring artists avoid ownership disputes and unpaid royalties",
  website: "https://www.mesawallet.io",
  logoSvg: `
    <svg width="200" height="100" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="black"/>
      <!-- MESA logo based on the actual branding -->
      <g transform="translate(40, 25)">
        <!-- Stylized "M" logo -->
        <path d="M0,10 L10,50 L20,20 L30,50 L40,10" 
              fill="none" stroke="#ff2d55" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
      </g>
      <!-- MESA text -->
      <text x="100" y="55" font-family="Arial" font-size="32" font-weight="bold" fill="white">mesa</text>
    </svg>
  `,
  established: "2023",
  tagline: "Your hit song could cost you everything"
};

// Generate a visual "tattoo" from the DID
function generateVisualTattoo(did, logoSvg) {
  // Create a unique pattern based on the DID hash
  const didHash = ethers.utils.id(did);
  const colors = [];
  
  // Extract colors from the hash
  for (let i = 0; i < 6; i++) {
    colors.push('#' + didHash.slice(2 + i * 6, 8 + i * 6));
  }
  
  // Generate a unique SVG pattern
  const svg = `
    <svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <rect width="40" height="40" fill="${colors[0]}"/>
          <circle cx="20" cy="20" r="15" fill="${colors[1]}"/>
          <rect x="10" y="10" width="20" height="20" fill="${colors[2]}" transform="rotate(45 20 20)"/>
        </pattern>
      </defs>
      <rect width="400" height="400" fill="url(#grid)"/>
      <circle cx="200" cy="200" r="150" fill="black"/>
      <g transform="translate(100, 150)">
        ${logoSvg}
      </g>
      <text x="100" y="270" font-family="monospace" font-size="14" fill="white">${did.slice(0, 20)}...</text>
      <text x="80" y="300" font-family="Arial" font-size="16" fill="white">Protecting Music Rights On Base</text>
      <text x="150" y="325" font-family="Arial" font-size="12" fill="#ff2d55">Verified Identity</text>
    </svg>
  `;
  
  return {
    svg,
    dataUri: `data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`
  };
}

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
    console.log("Starting MESA AI DID attestation process on Base Sepolia...");
    
    // Connect to Base Sepolia
    const provider = new ethers.providers.JsonRpcProvider("https://sepolia.base.org");
    
    // Load private key from environment variables
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
    
    // Generate DID for MESA AI
    // Format: did:base:mesa:{uniqueId}
    const mesaIdHash = ethers.utils.id(wallet.address + mesaInfo.name).slice(2, 14);
    const mesaDID = `did:base:mesa:${mesaIdHash}`;
    console.log(`Generated DID for MESA: ${mesaDID}`);
    
    // Generate visual tattoo
    console.log("Generating visual identity tattoo...");
    const visualTattoo = generateVisualTattoo(mesaDID, mesaInfo.logoSvg);
    console.log("Visual tattoo generated");
    
    // Step 1: Register a schema for DID attestations
    console.log("Registering DID schema...");
    
    // Define the schema string
    const schemaString = "string did, string name, string description, string website, string established, string visualIdentity";
    
    // Register the schema
    console.log("Submitting schema registration transaction...");
    const schemaTx = await schemaRegistry.register(
      schemaString,
      true, // revocable
      "Decentralized Identifier (DID) Attestation Schema for MESA Music Rights Protection",
      TX_OPTIONS
    );
    
    console.log(`Schema registration transaction submitted: ${schemaTx.hash}`);
    const schemaReceipt = await waitForTransaction(schemaTx);
    
    // Extract schema UID
    console.log("Debug - Schema Receipt Logs:", JSON.stringify(schemaReceipt.logs, null, 2));
    
    // Define schemaUID variable
    let schemaUID;
    
    // Try to extract from logs or use a fallback
    try {
      if (schemaReceipt.logs && schemaReceipt.logs.length > 0 && 
          schemaReceipt.logs[0].topics && schemaReceipt.logs[0].topics.length > 1) {
        schemaUID = "0x" + schemaReceipt.logs[0].topics[1].slice(26);
      } else {
        // Fallback to hardcoded schema
        schemaUID = "0x14554977234f8ef97a88c5a1da6d65e8522922671b511b4aa5d198a4629de6b1";
      }
    } catch (error) {
      console.log("Error extracting schema UID, using fallback");
      schemaUID = "0x14554977234f8ef97a88c5a1da6d65e8522922671b511b4aa5d198a4629de6b1";
    }
    
    console.log(`Using schema with UID: ${schemaUID}`);
    
    // Step 2: Create the DID attestation
    console.log("\nCreating MESA AI DID attestation...");
    
    // ABI encode the attestation data
    const abiCoder = new ethers.utils.AbiCoder();
    const encodedData = abiCoder.encode(
      ["string", "string", "string", "string", "string", "string"],
      [
        mesaDID,
        mesaInfo.name,
        mesaInfo.description,
        mesaInfo.website,
        mesaInfo.established,
        visualTattoo.dataUri
      ]
    );
    
    // Create attestation data object
    const attestationData = {
      schema: schemaUID,
      data: {
        recipient: wallet.address, // Self-attestation
        expirationTime: 0, // No expiration
        revocable: true,
        refUID: ethers.constants.HashZero,
        data: encodedData,
        value: 0
      }
    };
    
    console.log("Submitting DID attestation transaction...");
    const attestTx = await eas.attest(attestationData, TX_OPTIONS);
    
    console.log(`DID attestation transaction submitted: ${attestTx.hash}`);
    const attestReceipt = await waitForTransaction(attestTx);
    
    // Extract attestation UID
    let attestationUID = attestReceipt.transactionHash;
    
    try {
      if (attestReceipt.logs && attestReceipt.logs.length > 0 && 
          attestReceipt.logs[0].topics && attestReceipt.logs[0].topics.length > 1) {
        attestationUID = "0x" + attestReceipt.logs[0].topics[1].slice(26);
      }
    } catch (error) {
      console.log("Error extracting attestation UID, using transaction hash");
    }
    
    console.log("\n=== DID Attestation Successful ===");
    console.log(`DID: ${mesaDID}`);
    console.log(`Attestation UID: ${attestationUID}`);
    console.log(`Transaction Hash: ${attestReceipt.transactionHash}`);
    console.log(`Block Number: ${attestReceipt.blockNumber}`);
    
    console.log("\nView your DID attestation on Base Sepolia EAS Explorer:");
    console.log(`https://base-sepolia.easscan.org/attestation/view/${attestationUID}`);
    
    // Save the visual tattoo SVG to a file
    const fs = require('fs');
    fs.writeFileSync('MESA_DID_visual_tattoo.svg', visualTattoo.svg);
    console.log("\nVisual identity tattoo saved to MESA_DID_visual_tattoo.svg");
    
    console.log("\nFor verification purposes, here is the base64 data URI of the visual tattoo:");
    console.log(visualTattoo.dataUri.slice(0, 100) + "...");
    
    console.log("\nSuccess! MESA now has a decentralized identifier (DID) on Base Sepolia.");
    console.log(`This DID can be used to verify MESA's identity and services for music rights protection.`);
    console.log(`Visit ${mesaInfo.website} to learn more about MESA's music rights protection services.`);
    
  } catch (error) {
    console.error("Error creating DID attestation:");
    console.error(error);
    process.exit(1);
  }
}

main(); 