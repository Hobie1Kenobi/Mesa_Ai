const { ethers } = require('ethers');

// EAS contract addresses on Base Sepolia
const EAS_CONTRACT_ADDRESS = '0xC2679fBD37d54388Ce493F1DB75320D236e1815e';
const SCHEMA_REGISTRY_ADDRESS = '0x0a7E2Ff54e76B8E6659aedc9103FB21c038050D0';

// ABIs (simplified with only the methods we need)
const EAS_ABI = [
  "function attest(tuple(bytes32 schema, tuple(address recipient, uint64 expirationTime, bool revocable, bytes32 refUID, bytes data, uint256 value) data)) external payable returns (bytes32)",
  "function getAttestation(bytes32 uid) external view returns (tuple(bytes32 uid, bytes32 schema, address recipient, address attester, bool revocable, bytes32 refUID, uint64 timeCreated, uint64 expirationTime, bytes data))",
  "function isAttestationRevoked(bytes32 uid) external view returns (bool)"
];

const SCHEMA_REGISTRY_ABI = [
  "function register(string calldata schema, bool revocable, string calldata description) external returns (bytes32)",
  "function getSchema(bytes32 uid) external view returns (tuple(bytes32 uid, bool revocable, string schema, string description))"
];

async function queryAttestation(attestationUID) {
  try {
    console.log(`Querying attestation UID: ${attestationUID}`);
    
    // Connect to Base Sepolia
    const provider = new ethers.providers.JsonRpcProvider("https://sepolia.base.org");
    
    // Connect to EAS contract (read-only)
    const eas = new ethers.Contract(
      EAS_CONTRACT_ADDRESS,
      EAS_ABI,
      provider
    );
    
    // Get attestation
    const attestation = await eas.getAttestation(attestationUID);
    
    console.log("\n=== Attestation Data ===");
    console.log("UID:", attestation.uid);
    console.log("Schema:", attestation.schema);
    console.log("Recipient:", attestation.recipient);
    console.log("Attester:", attestation.attester);
    console.log("Time Created:", new Date(attestation.timeCreated.toNumber() * 1000).toISOString());
    console.log("Is Revocable:", attestation.revocable);
    console.log("Is Revoked:", await eas.isAttestationRevoked(attestationUID));
    
    // Get schema information
    const schemaRegistry = new ethers.Contract(
      SCHEMA_REGISTRY_ADDRESS,
      SCHEMA_REGISTRY_ABI,
      provider
    );
    
    const schema = await schemaRegistry.getSchema(attestation.schema);
    console.log("\n=== Schema Information ===");
    console.log("Schema UID:", schema.uid);
    console.log("Schema Definition:", schema.schema);
    console.log("Description:", schema.description);
    console.log("Is Revocable:", schema.revocable);
    
    // Try to decode the data based on schema
    try {
      console.log("\n=== Decoded Data ===");
      // This is a simplified approach to decoding
      // In a real implementation, you'd use the SchemaEncoder from the EAS SDK
      console.log("Raw Data:", attestation.data);
      console.log("Note: For proper decoding, use the EAS SDK's SchemaEncoder");
    } catch (decodeError) {
      console.error("Error decoding data:", decodeError.message);
    }
    
    console.log("\nView on EAS Explorer:");
    console.log(`https://base-sepolia.easscan.org/attestation/view/${attestationUID}`);
    
    return attestation;
  } catch (error) {
    console.error('Error querying attestation:', error.message);
  }
}

async function listSchemas() {
  try {
    console.log("Listing registered schemas relevant to music rights...");
    
    // Note: EAS doesn't provide a direct way to list all schemas
    // In a real implementation, you would maintain a list of known schemas
    // or query them from a subgraph or indexer
    
    console.log("\nCommon Music Rights Schemas on Base Sepolia:");
    console.log("- 0x0d8026ba54409df0a7ecf71c9e0a29e8f2faaf3ea12b138d0a0c1ecf69c7ca98: Music Rights Schema");
    
    console.log("\nUse querySchema to get details of a specific schema");
  } catch (error) {
    console.error('Error listing schemas:', error.message);
  }
}

async function querySchema(schemaUID) {
  try {
    console.log(`Querying schema UID: ${schemaUID}`);
    
    // Connect to Base Sepolia
    const provider = new ethers.providers.JsonRpcProvider("https://sepolia.base.org");
    
    // Connect to Schema Registry contract
    const schemaRegistry = new ethers.Contract(
      SCHEMA_REGISTRY_ADDRESS,
      SCHEMA_REGISTRY_ABI,
      provider
    );
    
    // Get schema
    const schema = await schemaRegistry.getSchema(schemaUID);
    
    console.log("\n=== Schema Information ===");
    console.log("Schema UID:", schema.uid);
    console.log("Schema Definition:", schema.schema);
    console.log("Description:", schema.description);
    console.log("Is Revocable:", schema.revocable);
    
    console.log("\nView on EAS Explorer:");
    console.log(`https://base-sepolia.easscan.org/schema/${schemaUID}`);
    
    return schema;
  } catch (error) {
    console.error('Error querying schema:', error.message);
  }
}

// Main function to handle command line arguments
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  
  if (!command) {
    console.log(`
MESA AI Guardian EAS Direct CLI
Usage:
  node eas-direct.js <command> [arguments]

Commands:
  query <attestationUID>    Query an attestation by UID
  schemas                   List relevant schema UIDs for music rights
  schema <schemaUID>        Query schema details by UID
`);
    return;
  }
  
  switch (command) {
    case 'query':
      if (!args[1]) {
        console.error('Please provide an attestation UID');
        return;
      }
      await queryAttestation(args[1]);
      break;
      
    case 'schemas':
      await listSchemas();
      break;
      
    case 'schema':
      if (!args[1]) {
        console.error('Please provide a schema UID');
        return;
      }
      await querySchema(args[1]);
      break;
      
    default:
      console.error(`Unknown command: ${command}`);
      break;
  }
}

main(); 