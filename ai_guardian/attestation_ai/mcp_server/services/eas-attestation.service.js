/**
 * EAS Attestation Service
 * 
 * Service for interacting with Ethereum Attestation Service (EAS).
 * Provides functionality for creating, verifying, and revoking attestations.
 */

const { EAS, SchemaEncoder } = require('@ethereum-attestation-service/eas-sdk');
const { ethers } = require('ethers');
const config = require('../config');

class EASAttestationService {
  constructor() {
    this.initialized = false;
    this.provider = null;
    this.signer = null;
    this.eas = null;
    this.schemaRegistry = null;
    this.schemaUID = null;
    this.schemaEncoder = null;
  }

  /**
   * Initialize the service with ethereum provider and signer
   * @param {string} privateKey - Private key for signing transactions (optional)
   * @returns {Promise<boolean>} - True if initialization was successful
   */
  async initialize(privateKey) {
    try {
      // Set up provider
      this.provider = new ethers.providers.JsonRpcProvider(config.blockchain.rpcUrl);
      
      // Set up signer if private key is provided
      if (privateKey) {
        this.signer = new ethers.Wallet(privateKey, this.provider);
      } else if (process.env.ATTESTATION_PRIVATE_KEY) {
        this.signer = new ethers.Wallet(process.env.ATTESTATION_PRIVATE_KEY, this.provider);
      } else {
        console.warn('No private key provided for EAS attestation service. Read-only mode activated.');
        this.signer = this.provider;
      }
      
      // Initialize EAS
      this.eas = new EAS(config.blockchain.easAddress);
      this.eas.connect(this.signer);
      
      // Use schema from config
      this.schemaUID = config.eas.musicContentSchema.uid;
      
      // Initialize schema encoder
      this.schemaEncoder = new SchemaEncoder(config.eas.musicContentSchema.schema);
      
      this.initialized = true;
      console.log('EAS Attestation Service initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize EAS Attestation Service:', error);
      return false;
    }
  }

  /**
   * Create a new attestation for music content
   * @param {object} contentData - Content data to attest
   * @param {string} contentData.contentId - Unique identifier for the content
   * @param {string} contentData.title - Content title
   * @param {string} contentData.artist - Artist name
   * @param {string} contentData.publisher - Publisher name
   * @param {number} contentData.creationYear - Year of creation
   * @param {string} contentData.metadataURI - URI pointing to additional metadata
   * @param {boolean} contentData.isOriginal - Whether this is original content
   * @param {string} recipient - Recipient address (defaults to self-attestation)
   * @returns {Promise<object>} - Transaction receipt and attestation details
   */
  async createMusicAttestation(contentData, recipient) {
    if (!this.initialized) {
      await this.initialize();
    }

    try {
      if (!this.schemaUID || this.schemaUID === '') {
        throw new Error('Schema UID not configured. Please set MUSIC_CONTENT_SCHEMA_UID in environment variables.');
      }

      // Convert contentId to bytes32 if it's a string
      let contentIdBytes;
      if (typeof contentData.contentId === 'string') {
        // If it's already 0x-prefixed and 66 chars long, assume it's already bytes32
        if (contentData.contentId.startsWith('0x') && contentData.contentId.length === 66) {
          contentIdBytes = contentData.contentId;
        } else {
          // Otherwise hash it to create bytes32
          contentIdBytes = ethers.utils.id(contentData.contentId);
        }
      } else {
        throw new Error('Invalid contentId format');
      }

      // Encode the data using schema encoder
      const encodedData = this.schemaEncoder.encodeData([
        { name: 'contentId', value: contentIdBytes, type: 'bytes32' },
        { name: 'title', value: contentData.title, type: 'string' },
        { name: 'artist', value: contentData.artist, type: 'string' },
        { name: 'publisher', value: contentData.publisher, type: 'string' },
        { name: 'creationYear', value: contentData.creationYear, type: 'uint256' },
        { name: 'metadataURI', value: contentData.metadataURI || '', type: 'string' },
        { name: 'isOriginal', value: contentData.isOriginal, type: 'bool' }
      ]);

      // Default to self-attestation if no recipient provided
      const recipientAddress = recipient || await this.signer.getAddress();

      // Transaction options
      const tx = await this.eas.attest({
        schema: this.schemaUID,
        data: {
          recipient: recipientAddress,
          expirationTime: 0, // No expiration
          revocable: true,   // Can be revoked later if needed
          data: encodedData
        }
      });

      // Wait for transaction to be mined
      const receipt = await tx.wait();

      // Process the receipt to extract the attestation UID
      let attestationUID = null;
      if (receipt && receipt.logs) {
        // Find the Attested event and extract UID
        for (const log of receipt.logs) {
          try {
            const parsedLog = this.eas.interface.parseLog(log);
            if (parsedLog.name === 'Attested') {
              attestationUID = parsedLog.args.uid;
              break;
            }
          } catch (e) {
            // Skip logs that can't be parsed
            continue;
          }
        }
      }

      return {
        success: true,
        transactionHash: receipt.transactionHash,
        blockNumber: receipt.blockNumber,
        attestationUID,
        explorerLink: `${config.blockchain.blockExplorerUrl}/tx/${receipt.transactionHash}`
      };
    } catch (error) {
      console.error('Failed to create attestation:', error);
      throw new Error(`Attestation creation failed: ${error.message}`);
    }
  }

  /**
   * Verify an attestation exists and is valid
   * @param {string} uid - Attestation UID to verify
   * @returns {Promise<object>} - Verification result and attestation data
   */
  async verifyAttestation(uid) {
    if (!this.initialized) {
      await this.initialize();
    }

    try {
      // Get the attestation data from EAS
      const attestation = await this.eas.getAttestation(uid);
      
      if (!attestation) {
        return {
          isValid: false,
          message: 'Attestation not found'
        };
      }

      // Check if the attestation is revoked
      if (attestation.revoked) {
        return {
          isValid: false,
          message: 'Attestation has been revoked',
          attestation
        };
      }

      // Check if the attestation has expired (if applicable)
      if (attestation.expirationTime > 0) {
        const currentTime = Math.floor(Date.now() / 1000);
        if (currentTime > attestation.expirationTime) {
          return {
            isValid: false,
            message: 'Attestation has expired',
            attestation
          };
        }
      }

      // Decode the attestation data
      const decodedData = this.schemaEncoder.decodeData(attestation.data);
      
      // Return verification result with decoded data
      return {
        isValid: true,
        message: 'Attestation is valid',
        attestation,
        data: this._formatDecodedData(decodedData)
      };
    } catch (error) {
      console.error('Failed to verify attestation:', error);
      throw new Error(`Attestation verification failed: ${error.message}`);
    }
  }

  /**
   * Revoke an attestation
   * @param {string} uid - Attestation UID to revoke
   * @returns {Promise<object>} - Transaction receipt
   */
  async revokeAttestation(uid) {
    if (!this.initialized) {
      await this.initialize();
    }

    try {
      // Ensure we have a signer with a private key
      if (this.signer === this.provider) {
        throw new Error('Private key required for revocation. Read-only mode is active.');
      }

      // Get the attestation to verify it exists and check permissions
      const attestation = await this.eas.getAttestation(uid);
      
      if (!attestation) {
        throw new Error('Attestation not found');
      }
      
      // Check if already revoked
      if (attestation.revoked) {
        return {
          success: true,
          message: 'Attestation was already revoked',
          uid
        };
      }
      
      // Check if attester is the same as the signer
      const signerAddress = await this.signer.getAddress();
      if (attestation.attester.toLowerCase() !== signerAddress.toLowerCase()) {
        throw new Error('Only the original attester can revoke an attestation');
      }

      // Revoke the attestation
      const tx = await this.eas.revoke({
        schema: this.schemaUID,
        data: {
          uid
        }
      });

      // Wait for transaction to be mined
      const receipt = await tx.wait();

      return {
        success: true,
        uid,
        transactionHash: receipt.transactionHash,
        blockNumber: receipt.blockNumber,
        explorerLink: `${config.blockchain.blockExplorerUrl}/tx/${receipt.transactionHash}`
      };
    } catch (error) {
      console.error('Failed to revoke attestation:', error);
      throw new Error(`Attestation revocation failed: ${error.message}`);
    }
  }

  /**
   * Get attestation status and data
   * @param {string} uid - Attestation UID
   * @returns {Promise<object>} - Attestation status and data
   */
  async getAttestationStatus(uid) {
    if (!this.initialized) {
      await this.initialize();
    }

    try {
      // Get the attestation data from EAS
      const attestation = await this.eas.getAttestation(uid);
      
      if (!attestation) {
        return {
          exists: false,
          message: 'Attestation not found'
        };
      }

      // Decode the attestation data
      const decodedData = this.schemaEncoder.decodeData(attestation.data);
      
      // Return verification result with decoded data
      return {
        exists: true,
        isValid: !attestation.revoked,
        revoked: attestation.revoked,
        expirationTime: attestation.expirationTime > 0 
          ? new Date(attestation.expirationTime * 1000).toISOString()
          : null,
        attester: attestation.attester,
        recipient: attestation.recipient,
        time: new Date(attestation.time * 1000).toISOString(),
        data: this._formatDecodedData(decodedData)
      };
    } catch (error) {
      console.error('Failed to get attestation status:', error);
      throw new Error(`Failed to get attestation status: ${error.message}`);
    }
  }

  /**
   * Format decoded attestation data for easier consumption
   * @private
   * @param {Array} decodedData - Raw decoded data from schema encoder
   * @returns {object} - Formatted data object
   */
  _formatDecodedData(decodedData) {
    const formattedData = {};
    
    for (const item of decodedData) {
      // Handle special conversions
      if (item.name === 'contentId' && item.type === 'bytes32') {
        formattedData[item.name] = item.value.value;
      } else if (item.name === 'creationYear' && item.type === 'uint256') {
        formattedData[item.name] = parseInt(item.value.toString());
      } else if (item.type === 'bool') {
        formattedData[item.name] = Boolean(item.value);
      } else {
        formattedData[item.name] = item.value;
      }
    }
    
    return formattedData;
  }

  /**
   * Mock attestation creation for testing environments
   * @param {object} contentData - Content data to attest
   * @returns {Promise<object>} - Mock transaction receipt and attestation details
   */
  async mockCreateAttestation(contentData) {
    if (!config.isTest && !config.mockMode) {
      throw new Error('Mock methods should only be used in test environments');
    }
    
    // Generate a mock UID
    const mockUID = '0x' + Array(64).fill(0).map(() => 
      Math.floor(Math.random() * 16).toString(16)).join('');
    
    return {
      success: true,
      transactionHash: '0x' + Array(64).fill(0).map(() => 
        Math.floor(Math.random() * 16).toString(16)).join(''),
      blockNumber: Math.floor(Math.random() * 10000000),
      attestationUID: mockUID,
      explorerLink: `${config.blockchain.blockExplorerUrl}/tx/mock-tx-hash`,
      mock: true
    };
  }
}

module.exports = new EASAttestationService(); 