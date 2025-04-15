const { ethers } = require('ethers');
require('dotenv').config();

// Minimal ABI for the EAS contract - just what we need for attestations
const EAS_ABI = [
  "function attest(tuple(bytes32 schema, tuple(address recipient, uint64 expirationTime, bool revocable, bytes32 refUID, bytes data, uint256 value) data)) external payable returns (bytes32)",
  "function getAttestation(bytes32 uid) external view returns (tuple(bytes32 uid, bytes32 schema, address recipient, address attester, bool revocable, bytes32 refUID, uint64 timestamp, uint64 expirationTime, bytes data))",
  "event Attested(bytes32 indexed uid, address indexed recipient, address indexed attester, bytes32 schema, uint64 expirationTime, bool revocable, bytes32 refUID, bytes data)"
];

class EASAttestationService {
  constructor() {
    // Base Sepolia configuration
    this.provider = new ethers.providers.JsonRpcProvider(
      process.env.BASE_SEPOLIA_RPC_URL || "https://sepolia.base.org"
    );
    
    if (!process.env.PRIVATE_KEY) {
      throw new Error('PRIVATE_KEY must be set in .env file');
    }
    
    this.wallet = new ethers.Wallet(process.env.PRIVATE_KEY, this.provider);
    console.log(`EAS Service initialized with wallet: ${this.wallet.address}`);
    
    // EAS contract configuration
    this.easContractAddress = process.env.EAS_CONTRACT_ADDRESS || '0xC2679fBD37d54388Ce493F1DB75320D236e1815e';
    this.easContract = new ethers.Contract(this.easContractAddress, EAS_ABI, this.wallet);
    
    // Get the schema UID from the environment or configuration
    this.schemaUID = process.env.ENHANCED_SCHEMA_UID;
    
    // Attempt to load from schema_config.json if not in environment
    if (!this.schemaUID) {
      try {
        const fs = require('fs');
        const configPath = './schema_config.json';
        
        if (fs.existsSync(configPath)) {
          const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
          this.schemaUID = config.schemaUID;
          console.log(`Loaded schema UID from config: ${this.schemaUID}`);
        } else {
          console.warn('schema_config.json not found');
        }
      } catch (error) {
        console.error('Error loading schema from config:', error);
      }
    }
    
    if (!this.schemaUID) {
      throw new Error('ENHANCED_SCHEMA_UID must be set in .env file or schema_config.json');
    }
  }
  
  async createAttestation(data) {
    console.log(`Creating attestation for ${data.track_title} by ${data.artist_name}...`);
    
    // Ensure the wallet address is a proper Ethereum address
    const recipientAddress = this._ensureValidAddress(data.wallet_address);
    
    // Format all fields in the correct order according to our schema
    const fields = [
      data.track_title,
      data.artist_name, 
      data.publisher,
      data.rights_type,
      data.jurisdiction,
      data.rightsholder_name,
      data.rightsholder_email,
      data.rightsholder_role,
      data.rightsholder_ipi,
      data.split_percentage,
      data.rightsholder_address,
      data.rightsholder_phone,
      data.rightsholder_id,
      data.iswc_code,
      data.isrc_code,
      data.designated_administrator,
      recipientAddress,
      data.mesa_verified
    ];
    
    // Field types matching the schema
    const types = [
      'string', 'string', 'string',             // track_title, artist_name, publisher
      'string', 'string',                        // rights_type, jurisdiction
      'string', 'string', 'string', 'string',    // rightsholder details
      'string', 'string', 'string', 'string',    // more rightsholder details
      'string', 'string', 'string',              // iswc, isrc, administrator
      'address',                                 // wallet_address (as actual address type)
      'string'                                   // mesa_verified
    ];
    
    // Create ABI-encoded data for the attestation
    const abiCoder = new ethers.utils.AbiCoder();
    const encodedData = abiCoder.encode(types, fields);
    
    // Prepare transaction
    const attestationData = {
      schema: this.schemaUID,
      data: {
        recipient: recipientAddress,
        expirationTime: 0,        // No expiration
        revocable: true,          // Can be revoked if needed
        refUID: ethers.constants.HashZero,  // No reference UID
        data: encodedData,
        value: 0                  // No ETH value
      }
    };
    
    // Transaction options
    const txOptions = {
      gasLimit: 1000000,
      gasPrice: ethers.utils.parseUnits('10', 'gwei')
    };
    
    try {
      console.log('Submitting attestation transaction...');
      const tx = await this.easContract.attest(attestationData, txOptions);
      console.log(`Transaction submitted: ${tx.hash}`);
      
      // Wait for transaction to be mined
      const receipt = await this._waitForTransaction(tx);
      console.log(`Transaction confirmed in block ${receipt.blockNumber}`);
      
      // Extract attestation UID from logs using event parsing
      let attestationUID = null;
      
      for (const log of receipt.logs) {
        try {
          const parsedLog = this.easContract.interface.parseLog(log);
          if (parsedLog.name === 'Attested') {
            attestationUID = parsedLog.args.uid;
            break;
          }
        } catch (error) {
          // Skip logs that can't be parsed
          continue;
        }
      }
      
      // If we couldn't extract the UID from the logs, use a fallback
      if (!attestationUID) {
        console.warn('Could not extract attestation UID from logs, using transaction hash as fallback');
        attestationUID = receipt.transactionHash;
      }
      
      return {
        attestationUID,
        transactionHash: receipt.transactionHash,
        blockNumber: receipt.blockNumber,
        gasUsed: receipt.gasUsed.toString()
      };
    } catch (error) {
      console.error('Error creating attestation:', error);
      throw new Error(`Failed to create attestation: ${error.message}`);
    }
  }
  
  async _waitForTransaction(tx, timeoutSeconds = 180) {
    console.log(`Waiting for transaction ${tx.hash} to be confirmed (timeout: ${timeoutSeconds}s)...`);
    
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Transaction confirmation timed out after ${timeoutSeconds} seconds`));
      }, timeoutSeconds * 1000);
      
      tx.wait()
        .then((receipt) => {
          clearTimeout(timeout);
          resolve(receipt);
        })
        .catch((error) => {
          clearTimeout(timeout);
          reject(error);
        });
    });
  }
  
  _ensureValidAddress(address) {
    try {
      // Make sure it's a valid Ethereum address
      return ethers.utils.getAddress(address);
    } catch (error) {
      // If it's not valid, use the wallet address
      console.warn(`Invalid address provided: ${address}, using wallet address instead`);
      return this.wallet.address;
    }
  }
  
  async verifyAttestation(uid) {
    try {
      console.log(`Verifying attestation with UID: ${uid}`);
      const attestation = await this.easContract.getAttestation(uid);
      
      const isValid = attestation && attestation.attester !== ethers.constants.AddressZero;
      console.log(`Attestation validation result: ${isValid}`);
      
      return {
        isValid,
        attestation
      };
    } catch (error) {
      console.error('Error verifying attestation:', error);
      return {
        isValid: false,
        error: error.message
      };
    }
  }
}

// Allow direct execution for testing
if (require.main === module) {
  const test = async () => {
    try {
      // Only run test if schema UID is provided via command line
      const schemaUID = process.argv[2];
      if (!schemaUID) {
        console.error('Please provide a schema UID as a command line argument');
        process.exit(1);
      }
      
      process.env.ENHANCED_SCHEMA_UID = schemaUID;
      
      console.log('Testing EAS Attestation Service...');
      const service = new EASAttestationService();
      
      const sampleData = {
        track_title: 'Test Track via API',
        artist_name: 'Test Artist',
        publisher: 'Test Publisher',
        rights_type: 'both',
        jurisdiction: 'International',
        rightsholder_name: 'Test Rights Holder',
        rightsholder_email: 'test@example.com',
        rightsholder_role: 'Composer',
        rightsholder_ipi: '00000000000',
        split_percentage: '100',
        rightsholder_address: '123 Test St',
        rightsholder_phone: '+1234567890',
        rightsholder_id: 'TEST-ID-123',
        iswc_code: 'T-000000000-0',
        isrc_code: 'USTEST00000',
        designated_administrator: 'MESA Admin',
        wallet_address: process.env.WALLET_ADDRESS,
        mesa_verified: 'true'
      };
      
      // Create a test attestation
      const result = await service.createAttestation(sampleData);
      console.log('Attestation created:', result);
      
      // Verify the attestation
      const verification = await service.verifyAttestation(result.attestationUID);
      console.log('Verification result:', verification.isValid);
      
      console.log('\nView attestation at:');
      console.log(`https://base-sepolia.easscan.org/attestation/view/${result.attestationUID}`);
      
    } catch (error) {
      console.error('Test failed:', error);
    }
  };
  
  test();
}

module.exports = EASAttestationService; 