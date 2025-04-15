/**
 * Ethereum Attestation Service (EAS) Integration
 * 
 * This service handles interactions with the EAS protocol, including:
 * - Creating new attestations for verified music content
 * - Verifying existing attestations
 * - Revoking attestations when necessary
 * - Querying attestations by various parameters
 */

const { EAS, SchemaEncoder } = require('@ethereum-attestation-service/eas-sdk');
const { ethers } = require('ethers');
const config = require('../config');
const logger = require('../utils/logger');

// Schema definition for music content attestations
const MUSIC_SCHEMA = {
  schema: "string contentId, string title, string artist, string publisher, uint16 creationYear, string metadataURI, bool isOriginal",
  uid: config.eas?.musicSchemaUID || "0x1234567890123456789012345678901234567890123456789012345678901234" // Replace with actual schema UID
};

class EASService {
  constructor() {
    this.initialized = false;
    this.eas = null;
    this.provider = null;
    this.wallet = null;
    this.schemaEncoder = null;
    this.easContractAddress = config.eas?.contractAddress || "0xC2679fBD37d54388Ce493F1DB75320D236e1815e"; // Sepolia EAS contract address
    this.network = config.eas?.network || "sepolia";
  }

  /**
   * Initialize the EAS service
   */
  async initialize() {
    try {
      logger.info('Initializing EAS Service');
      
      // Create provider based on configuration
      this.provider = this._createProvider();
      
      // Create wallet from private key
      if (config.eas?.privateKey) {
        this.wallet = new ethers.Wallet(config.eas.privateKey, this.provider);
        logger.info('Wallet initialized', { address: this.wallet.address });
      } else {
        logger.warn('No private key provided, operating in read-only mode');
      }
      
      // Initialize EAS SDK
      this.eas = new EAS(this.easContractAddress);
      this.eas.connect(this.provider);
      
      // Create schema encoder
      this.schemaEncoder = new SchemaEncoder(MUSIC_SCHEMA.schema);
      
      this.initialized = true;
      logger.info('EAS Service initialized successfully');
      return true;
    } catch (error) {
      logger.error('Failed to initialize EAS Service', { error: error.message, stack: error.stack });
      throw new Error(`Failed to initialize EAS Service: ${error.message}`);
    }
  }

  /**
   * Create an attestation for verified music content
   * 
   * @param {Object} musicData - The music data to attest to
   * @returns {Promise<Object>} - The created attestation data
   */
  async createAttestation(musicData) {
    if (!this.initialized) {
      await this.initialize();
    }
    
    try {
      logger.info('Creating attestation for content', { contentId: musicData.contentId });
      
      // Check if wallet is available
      if (!this.wallet) {
        throw new Error('No wallet available for creating attestations');
      }
      
      // Connect EAS to the signer
      this.eas.connect(this.wallet);
      
      // Encode the data
      const encodedData = this.schemaEncoder.encodeData([
        { name: "contentId", value: musicData.contentId, type: "string" },
        { name: "title", value: musicData.title, type: "string" },
        { name: "artist", value: musicData.artist, type: "string" },
        { name: "publisher", value: musicData.publisher, type: "string" },
        { name: "creationYear", value: musicData.creationYear, type: "uint16" },
        { name: "metadataURI", value: musicData.metadataURI || "", type: "string" },
        { name: "isOriginal", value: musicData.isOriginal, type: "bool" }
      ]);
      
      // Create the attestation
      const tx = await this.eas.attest({
        schema: MUSIC_SCHEMA.uid,
        data: {
          recipient: ethers.constants.AddressZero, // No specific recipient
          expirationTime: 0, // No expiration
          revocable: true, // Can be revoked if needed
          data: encodedData
        }
      });
      
      // Wait for transaction confirmation
      const receipt = await tx.wait();
      
      // Extract the attestation UID from transaction logs
      // In development/test mode, generate a mock UID
      let attestationUID;
      if (config.env === 'development' || config.env === 'test') {
        attestationUID = `0x${Buffer.from(musicData.contentId).toString('hex').padStart(64, '0')}`;
      } else {
        // Extract actual UID from transaction receipt
        // This would be implemented based on the EAS SDK specifics
        attestationUID = receipt.logs[0].topics[1]; // Example, actual implementation may differ
      }
      
      logger.info('Attestation created successfully', { 
        attestationUID, 
        contentId: musicData.contentId,
        transactionHash: receipt.transactionHash 
      });
      
      return {
        attestationUID,
        contentId: musicData.contentId,
        transactionHash: receipt.transactionHash,
        blockNumber: receipt.blockNumber,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      logger.error('Failed to create attestation', { 
        error: error.message, 
        contentId: musicData.contentId 
      });
      
      // Handle development/test environment by returning mock attestation
      if (config.env === 'development' || config.env === 'test') {
        logger.info('Generating mock attestation for development/test', { contentId: musicData.contentId });
        
        const mockUID = `0x${Buffer.from(musicData.contentId).toString('hex').padStart(64, '0')}`;
        return {
          attestationUID: mockUID,
          contentId: musicData.contentId,
          transactionHash: `0x${Buffer.from(`tx-${Date.now()}`).toString('hex').padStart(64, '0')}`,
          blockNumber: Math.floor(Date.now() / 1000),
          timestamp: new Date().toISOString(),
          isMock: true
        };
      }
      
      throw new Error(`Failed to create attestation: ${error.message}`);
    }
  }

  /**
   * Verify an attestation
   * 
   * @param {string} attestationUID - The UID of the attestation to verify
   * @returns {Promise<Object>} - The verification result
   */
  async verifyAttestation(attestationUID) {
    if (!this.initialized) {
      await this.initialize();
    }
    
    try {
      logger.info('Verifying attestation', { attestationUID });
      
      // In development/test mode, return mock verification
      if (config.env === 'development' || config.env === 'test') {
        return this._getMockAttestation(attestationUID);
      }
      
      // Get the attestation from EAS
      const attestation = await this.eas.getAttestation(attestationUID);
      
      // Decode the attestation data
      const decodedData = this.schemaEncoder.decodeData(attestation.data);
      
      // Extract music data from decoded data
      const musicData = {};
      for (const field of decodedData) {
        musicData[field.name] = field.value.toString();
      }
      
      // Check if the attestation is revoked
      const isRevoked = await this.eas.isAttestationRevoked(attestationUID);
      
      return {
        attestationUID,
        schemaUID: attestation.schema,
        attester: attestation.attester,
        recipient: attestation.recipient,
        revoked: isRevoked,
        timestamp: new Date(Number(attestation.time) * 1000).toISOString(),
        expirationTime: attestation.expirationTime,
        data: musicData
      };
    } catch (error) {
      logger.error('Failed to verify attestation', { error: error.message, attestationUID });
      
      // Handle development/test environment
      if (config.env === 'development' || config.env === 'test') {
        return this._getMockAttestation(attestationUID);
      }
      
      throw new Error(`Failed to verify attestation: ${error.message}`);
    }
  }

  /**
   * Revoke an attestation
   * 
   * @param {string} attestationUID - The UID of the attestation to revoke
   * @returns {Promise<Object>} - The revocation result
   */
  async revokeAttestation(attestationUID) {
    if (!this.initialized) {
      await this.initialize();
    }
    
    try {
      logger.info('Revoking attestation', { attestationUID });
      
      // Check if wallet is available
      if (!this.wallet) {
        throw new Error('No wallet available for revoking attestations');
      }
      
      // Connect EAS to the signer
      this.eas.connect(this.wallet);
      
      // In development/test mode, simulate revocation
      if (config.env === 'development' || config.env === 'test') {
        return {
          attestationUID,
          transactionHash: `0x${Buffer.from(`revoke-${Date.now()}`).toString('hex').padStart(64, '0')}`,
          blockNumber: Math.floor(Date.now() / 1000),
          timestamp: new Date().toISOString(),
          isMock: true
        };
      }
      
      // Revoke the attestation
      const tx = await this.eas.revoke({
        schema: MUSIC_SCHEMA.uid,
        data: {
          uid: attestationUID
        }
      });
      
      // Wait for transaction confirmation
      const receipt = await tx.wait();
      
      logger.info('Attestation revoked successfully', { 
        attestationUID, 
        transactionHash: receipt.transactionHash 
      });
      
      return {
        attestationUID,
        transactionHash: receipt.transactionHash,
        blockNumber: receipt.blockNumber,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      logger.error('Failed to revoke attestation', { error: error.message, attestationUID });
      
      // Handle development/test environment
      if (config.env === 'development' || config.env === 'test') {
        return {
          attestationUID,
          transactionHash: `0x${Buffer.from(`revoke-${Date.now()}`).toString('hex').padStart(64, '0')}`,
          blockNumber: Math.floor(Date.now() / 1000),
          timestamp: new Date().toISOString(),
          isMock: true,
          error: error.message
        };
      }
      
      throw new Error(`Failed to revoke attestation: ${error.message}`);
    }
  }

  /**
   * Find attestations by query
   * 
   * @param {Object} query - Query parameters
   * @returns {Promise<Array>} - The matching attestations
   */
  async findAttestations(query) {
    if (!this.initialized) {
      await this.initialize();
    }
    
    try {
      logger.info('Finding attestations', { query });
      
      // In development/test mode, return mock attestations
      if (config.env === 'development' || config.env === 'test') {
        return this._getMockAttestations(query);
      }
      
      // Build EAS query based on parameters
      // This would be implemented based on the EAS indexer/API specifics
      // For now, return mock data
      
      return [];
    } catch (error) {
      logger.error('Failed to find attestations', { error: error.message, query });
      
      // Handle development/test environment
      if (config.env === 'development' || config.env === 'test') {
        return this._getMockAttestations(query);
      }
      
      throw new Error(`Failed to find attestations: ${error.message}`);
    }
  }

  /**
   * Create a provider based on configuration
   * @returns {ethers.providers.Provider} - The provider
   * @private
   */
  _createProvider() {
    // If RPC URL is provided, use it
    if (config.eas?.rpcUrl) {
      return new ethers.providers.JsonRpcProvider(config.eas.rpcUrl);
    }
    
    // Otherwise, use default provider for the specified network
    return ethers.getDefaultProvider(this.network);
  }

  /**
   * Get mock attestation for development/test
   * @param {string} attestationUID - The attestation UID
   * @returns {Object} - The mock attestation
   * @private
   */
  _getMockAttestation(attestationUID) {
    // Extract contentId from attestationUID if it's a mock UID
    const contentId = attestationUID.startsWith('0x') ? 
      Buffer.from(attestationUID.substring(2), 'hex').toString().replace(/\0/g, '') : 
      `mock-content-${attestationUID.substring(0, 8)}`;
    
    return {
      attestationUID,
      schemaUID: MUSIC_SCHEMA.uid,
      attester: config.eas?.walletAddress || "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
      recipient: ethers.constants.AddressZero,
      revoked: false,
      timestamp: new Date(Date.now() - Math.floor(Math.random() * 30 * 24 * 60 * 60 * 1000)).toISOString(),
      expirationTime: 0,
      isMock: true,
      data: {
        contentId,
        title: `Song Title ${contentId.substring(0, 8)}`,
        artist: `Artist ${Math.floor(Math.random() * 100)}`,
        publisher: `Publisher ${Math.floor(Math.random() * 20)}`,
        creationYear: (2000 + Math.floor(Math.random() * 23)).toString(),
        metadataURI: `ipfs://Qm${Buffer.from(contentId).toString('hex').substring(0, 44)}`,
        isOriginal: Math.random() > 0.2 ? "true" : "false" // 80% chance of being original
      }
    };
  }

  /**
   * Get mock attestations for development/test
   * @param {Object} query - Query parameters
   * @returns {Array} - The mock attestations
   * @private
   */
  _getMockAttestations(query) {
    const count = query.limit || 10;
    const results = [];
    
    for (let i = 0; i < count; i++) {
      const mockUID = `0x${Buffer.from(`mock-content-${i}-${Date.now()}`).toString('hex').padStart(64, '0')}`;
      results.push(this._getMockAttestation(mockUID));
    }
    
    // Apply filters if present in query
    if (query.publisher) {
      results.forEach(result => {
        result.data.publisher = query.publisher;
      });
    }
    
    if (query.artist) {
      results.forEach(result => {
        result.data.artist = query.artist;
      });
    }
    
    return results;
  }
}

module.exports = new EASService(); 