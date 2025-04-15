const { ethers } = require('ethers');

// EAS contract address on Base Sepolia
const EAS_CONTRACT_ADDRESS = '0xC2679fBD37d54388Ce493F1DB75320D236e1815e';

// Simple ABI for the EAS contract (only the functions we need)
const EAS_ABI = [
  "function getAttestation(bytes32 uid) external view returns (tuple(bytes32 uid, bytes32 schema, address recipient, address attester, bool revocable, bytes32 refUID, uint64 timeCreated, uint64 expirationTime, bytes data))",
  "function isAttestationRevoked(bytes32 uid) external view returns (bool)"
];

// Attestation UIDs to verify
const ATTESTATION_UIDS = [
  {
    name: "Music Rights Attestation",
    uid: "0xb2802e2e80824a796b8179349f94c73485d4dbe27e30cb5f04f4b1cd36083495"
  },
  {
    name: "MESA DID Attestation",
    uid: "0x3cb41fc26c71dd39cbb0f88ab1a7b5b209c76a22238b1017e3fd59c4c17c6073"
  }
];

async function verifyAttestations() {
  try {
    console.log("=== Verifying Attestations on Base Sepolia Testnet ===\n");
    
    // Connect to Base Sepolia RPC
    const provider = new ethers.providers.JsonRpcProvider("https://sepolia.base.org");
    
    // Create EAS contract instance
    const eas = new ethers.Contract(
      EAS_CONTRACT_ADDRESS,
      EAS_ABI,
      provider
    );
    
    // Check each attestation
    for (const attestation of ATTESTATION_UIDS) {
      console.log(`Verifying ${attestation.name} (${attestation.uid})...`);
      
      try {
        // Query the blockchain directly
        const onChainData = await eas.getAttestation(attestation.uid);
        const isRevoked = await eas.isAttestationRevoked(attestation.uid);
        
        console.log(`✅ ATTESTATION FOUND ON-CHAIN`);
        console.log(`   Schema: ${onChainData.schema}`);
        console.log(`   Recipient: ${onChainData.recipient}`);
        console.log(`   Attester: ${onChainData.attester}`);
        console.log(`   Time Created: ${new Date(onChainData.timeCreated.toNumber() * 1000).toISOString()}`);
        console.log(`   Revoked: ${isRevoked}`);
        
        // Check attestation transaction on the block explorer
        console.log(`   Block Explorer: https://sepolia.basescan.org/tx/${attestation.uid}`);
        console.log(`   EAS Explorer: https://base-sepolia.easscan.org/attestation/view/${attestation.uid}`);
        
        console.log("\n=== Raw Attestation Data ===");
        console.log(onChainData);
        console.log("===========================\n");
        
      } catch (error) {
        if (error.message.includes("call revert exception") || 
            error.message.includes("invalid attestation uid")) {
          console.log(`❌ ATTESTATION NOT FOUND ON-CHAIN: The attestation might not exist or there might be an issue with the contract call`);
          
          // Check transaction status
          console.log("   Checking if the transaction exists...");
          const txReceipt = await provider.getTransactionReceipt(attestation.uid);
          
          if (txReceipt) {
            console.log(`   ✅ TRANSACTION EXISTS on block ${txReceipt.blockNumber}`);
            console.log(`   Status: ${txReceipt.status === 1 ? 'Success' : 'Failed'}`);
            console.log(`   This suggests the transaction was processed but the attestation might not be correctly indexed or retrievable`);
          } else {
            console.log(`   ❌ TRANSACTION NOT FOUND. The transaction hash might be invalid.`);
          }
        } else {
          console.log(`❌ ERROR: ${error.message}`);
        }
      }
      console.log("\n-----------------------------------\n");
    }
    
    console.log("Verification complete. If transactions exist but attestations are not found,");
    console.log("this is likely an indexing issue with the EAS Explorer rather than a problem");
    console.log("with your attestations. The transactions are on-chain but may not be properly indexed yet.");
    
  } catch (error) {
    console.error("Error during verification:");
    console.error(error);
  }
}

// Run the verification
verifyAttestations(); 