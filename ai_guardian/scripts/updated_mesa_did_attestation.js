const { ethers } = require('ethers');
require('dotenv').config();

// EAS contract addresses on Base Sepolia
const EAS_CONTRACT_ADDRESS = '0xC2679fBD37d54388Ce493F1DB75320D236e1815e';

// Transaction options
const TX_OPTIONS = {
  gasLimit: 500000,
  gasPrice: ethers.utils.parseUnits('10', 'gwei')
};

// ABIs
const EAS_ABI = [
  "function attest(tuple(bytes32 schema, tuple(address recipient, uint64 expirationTime, bool revocable, bytes32 refUID, bytes data, uint256 value) data)) external payable returns (bytes32)",
  "function getAttestation(bytes32 uid) external view returns (tuple(bytes32 uid, bytes32 schema, address recipient, address attester, bool revocable, bytes32 refUID, uint64 timeCreated, uint64 expirationTime, bytes data))",
  "function isAttestationRevoked(bytes32 uid) external view returns (bool)"
];

// The schema UID that was used for track attestation
const SCHEMA_UID = "0x40aad7f118ba0f4f36c2036190fdc9df7b8bad9299744d5033ed843b1b00e0aa";

// MESA brand information
const mesaInfo = {
  name: "MESA",
  description: "Protecting music rights with professional splits contracts and work-for-hire agreements, ensuring artists avoid ownership disputes and unpaid royalties",
  website: "https://www.mesawallet.io",
  established: "2023",
  tagline: "Your hit song could cost you everything",
  // Updated logo based on the image provided (pink outline M logo with white mesa text on black background)
  logoSvg: `
    <svg width="400" height="100" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="black"/>
      <!-- Stylized "M" logo in pink -->
      <g transform="translate(20, 15) scale(1.5)">
        <path d="M10,10 C10,10 20,10 40,10 C60,10 70,10 70,10 C70,10 70,20 70,40 C70,60 70,70 70,70 C70,70 60,70 40,70 C20,70 10,70 10,70 C10,70 10,60 10,40 C10,20 10,10 10,10 Z" 
              fill="none" stroke="#ff5a78" stroke-width="2" />
        <path d="M30,25 L30,55 M50,25 L50,55 M30,25 L40,40 L50,25" 
              fill="none" stroke="#ff5a78" stroke-width="2" />
      </g>
      <!-- MESA text -->
      <text x="180" y="60" font-family="Arial" font-size="42" font-weight="bold" fill="white">mesa</text>
    </svg>
  `
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
    <svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <rect width="40" height="40" fill="${colors[0]}"/>
          <circle cx="20" cy="20" r="15" fill="${colors[1]}"/>
          <rect x="10" y="10" width="20" height="20" fill="${colors[2]}" transform="rotate(45 20 20)"/>
        </pattern>
      </defs>
      <rect width="600" height="400" fill="url(#grid)"/>
      <circle cx="300" cy="200" r="150" fill="black"/>
      <g transform="translate(100, 150)">
        ${logoSvg}
      </g>
      <text x="150" y="320" font-family="monospace" font-size="14" fill="white">${did}</text>
      <text x="130" y="350" font-family="Arial" font-size="16" fill="white">Protecting Music Rights On Base</text>
      <text x="250" y="375" font-family="Arial" font-size="12" fill="#ff5a78">Verified Identity</text>
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
    console.log("Starting updated MESA DID attestation process on Base Sepolia...");
    
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
    
    // Generate DID for MESA
    // Format: did:base:mesa:{uniqueId}
    const mesaIdHash = ethers.utils.id(wallet.address + mesaInfo.name + Date.now()).slice(2, 14);
    const mesaDID = `did:base:mesa:${mesaIdHash}`;
    console.log(`Generated updated DID for MESA: ${mesaDID}`);
    
    // Generate visual tattoo with updated logo
    console.log("Generating updated visual identity tattoo...");
    const visualTattoo = generateVisualTattoo(mesaDID, mesaInfo.logoSvg);
    console.log("Visual tattoo generated with new branding");
    
    console.log(`Using existing music schema with UID: ${SCHEMA_UID}`);
    
    // Create the DID attestation
    console.log("\nCreating updated MESA DID attestation...");
    
    // Create rich metadata about MESA based on their website and services
    const mesaMetadata = {
      did: `did:base:mesa:${mesaIdHash}`,
      name: "MESA Music Rights Platform",
      description: "Protecting music rights through blockchain innovation and smart contracts",
      logo: "https://www.mesawallet.io/logo.png",
      website: "https://www.mesawallet.io",
      services: [
        {
          id: "contract-builder",
          name: "Music Contract Builder",
          description: "Create legally binding music rights contracts for splits and work-for-hire agreements"
        },
        {
          id: "rights-protection",
          name: "Blockchain Rights Protection",
          description: "Convert legal contracts into smart contracts for automatic, fair compensation"
        },
        {
          id: "creator-protection",
          name: "Creator AI Protection",
          description: "Use Web3 attestations to ensure authenticity and protect against unauthorized AI-generated music"
        },
        {
          id: "royalty-management",
          name: "Transparent Royalty Management",
          description: "Ensure all rights holders are automatically and fairly compensated through blockchain technology"
        }
      ],
      mission: "MESA empowers music creators to protect their rights and manage collaborations effectively. By streamlining the administrative process through smart contracts on the blockchain, MESA ensures transparent ownership and fair compensation for all contributors.",
      features: [
        "File organization and collaboration management",
        "Contract creation with DocuSign integration ($2 per contract)",
        "Blockchain-based rights verification",
        "Automatic payment distribution",
        "Protection against unauthorized AI-generated content"
      ],
      blockchain: {
        network: "Base",
        implementation: "Ethereum Attestation Service (EAS)",
        purpose: "Transparent and immutable music rights verification"
      },
      slogan: "Rebel Responsibly. Focus on your art while we grow your business."
    };
    
    // Convert the rich metadata to JSON string
    const metadataJSON = JSON.stringify(mesaMetadata);
    
    // ABI encode the attestation data (adapting to match the music schema structure)
    const abiCoder = new ethers.utils.AbiCoder();
    const encodedData = abiCoder.encode(
      ["string", "string", "string", "address", "uint256", "string"],
      [
        mesaDID, // Using the DID as the "title" 
        "MESA Music Rights Platform", // Organization name as "artist"
        "Protecting creator rights with blockchain", // Short description as "iswc"
        wallet.address, // Rights holder
        789, // A unique tokenId
        visualTattoo.dataUri // Using SVG data URI directly instead of metadata JSON
      ]
    );
    
    // Also save the metadata to a separate JSON file for reference
    const fs = require('fs');
    fs.writeFileSync('MESA_DID_metadata.json', metadataJSON);
    console.log("Metadata JSON saved to MESA_DID_metadata.json");
    
    // Create attestation data object
    const attestationData = {
      schema: SCHEMA_UID,
      data: {
        recipient: wallet.address, // Self-attestation
        expirationTime: 0, // No expiration
        revocable: true,
        refUID: ethers.constants.HashZero,
        data: encodedData,
        value: 0
      }
    };
    
    console.log("Submitting updated DID attestation transaction...");
    const attestTx = await eas.attest(attestationData, TX_OPTIONS);
    
    console.log(`DID attestation transaction submitted: ${attestTx.hash}`);
    const attestReceipt = await waitForTransaction(attestTx);
    
    // Use transaction hash as attestation UID
    const attestationUID = attestReceipt.transactionHash;
    
    console.log("\n=== Updated DID Attestation Successful ===");
    console.log(`DID: ${mesaDID}`);
    console.log(`Attestation UID: ${attestationUID}`);
    console.log(`Transaction Hash: ${attestReceipt.transactionHash}`);
    console.log(`Block Number: ${attestReceipt.blockNumber}`);
    console.log(`Gas Used: ${attestReceipt.gasUsed.toString()}`);
    
    console.log("\nView your DID attestation on Base Sepolia EAS Explorer:");
    console.log(`https://base-sepolia.easscan.org/attestation/view/${attestationUID}`);
    
    // Save the visual tattoo SVG to a file
    fs.writeFileSync('MESA_Updated_DID_visual_tattoo.svg', visualTattoo.svg);
    console.log("\nUpdated visual identity tattoo saved to MESA_Updated_DID_visual_tattoo.svg");
    
    console.log("\nSuccess! MESA now has an updated decentralized identifier (DID) on Base Sepolia");
    console.log(`using the same schema as music tracks for unified verification.`);
    
  } catch (error) {
    console.error("Error creating updated DID attestation:");
    console.error(error);
    process.exit(1);
  }
}

main(); 