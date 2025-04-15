/**
 * Rights Registration Service
 * 
 * This service handles interaction with the RightsVault smart contract for
 * registering and managing music rights on the blockchain.
 */

const { ethers } = require('ethers');
const RIGHTS_VAULT_ABI = require('../abis/RightsVault.json');
const config = require('../config');

class RightsRegistrationService {
  constructor() {
    this.initialized = false;
    this.provider = null;
    this.signer = null;
    this.rightsVaultContract = null;
    this.mockMode = process.env.NODE_ENV === 'test' || process.env.MOCK_BLOCKCHAIN === 'true';
  }

  /**
   * Initialize the rights registration service
   * @returns {Promise<boolean>} Initialization success status
   */
  async initialize() {
    try {
      console.log('[RightsReg] Initializing Rights Registration Service...');
      
      if (this.mockMode) {
        console.log('[RightsReg] Running in mock mode');
        this.initialized = true;
        return true;
      }
      
      // Set up provider
      const providerUrl = config.blockchain.rpcUrl;
      this.provider = new ethers.providers.JsonRpcProvider(providerUrl);
      
      // Set up signer with private key
      const privateKey = process.env.RIGHTS_REGISTRATION_PRIVATE_KEY || process.env.ATTESTATION_PRIVATE_KEY;
      if (!privateKey) {
        throw new Error('RIGHTS_REGISTRATION_PRIVATE_KEY environment variable not set');
      }
      this.signer = new ethers.Wallet(privateKey, this.provider);
      
      // Connect to RightsVault contract
      const rightsVaultAddress = config.blockchain.rightsVaultAddress;
      this.rightsVaultContract = new ethers.Contract(
        rightsVaultAddress,
        RIGHTS_VAULT_ABI,
        this.signer
      );
      
      this.initialized = true;
      console.log('[RightsReg] Rights Registration Service initialized successfully');
      return true;
    } catch (error) {
      console.error('[RightsReg] Error initializing Rights Registration Service:', error);
      throw error;
    }
  }

  /**
   * Register new music rights on the blockchain
   * @param {string} ownerAddress - Ethereum address of the rights owner
   * @param {Object} rightsData - Rights data to register
   * @param {string} attestationUid - UID of the related attestation
   * @returns {Promise<Object>} Registration details
   */
  async registerRights(ownerAddress, rightsData, attestationUid) {
    this._validateInitialized();
    
    try {
      console.log(`[RightsReg] Registering rights for content: ${rightsData.title} by ${rightsData.artist}`);
      
      if (this.mockMode) {
        return this._mockRegisterRights(ownerAddress, rightsData, attestationUid);
      }
      
      // Format metadata as JSON string
      const metadata = JSON.stringify({
        title: rightsData.title,
        artist: rightsData.artist,
        publisher: rightsData.publisher,
        year: rightsData.year,
        genre: rightsData.genre,
        additionalInfo: rightsData.additionalInfo || {}
      });
      
      // Create unique content ID if not provided
      const contentId = rightsData.contentId || this._generateContentId(rightsData);
      
      // Submit registration transaction
      const tx = await this.rightsVaultContract.registerRights(
        contentId,
        ownerAddress,
        metadata,
        attestationUid,
        { gasLimit: 500000 }
      );
      
      console.log(`[RightsReg] Registration transaction submitted: ${tx.hash}`);
      
      // Wait for transaction to be mined
      const receipt = await tx.wait();
      console.log(`[RightsReg] Registration confirmed in block ${receipt.blockNumber}`);
      
      // Find registration event
      const registrationEvent = receipt.events.find(e => e.event === 'RightsRegistered');
      const registeredId = registrationEvent.args.contentId;
      
      return {
        contentId: registeredId,
        txHash: receipt.transactionHash,
        blockNumber: receipt.blockNumber,
        ownerAddress: ownerAddress,
        attestationUid: attestationUid,
        timestamp: Math.floor(Date.now() / 1000)
      };
    } catch (error) {
      console.error('[RightsReg] Error registering rights:', error);
      throw error;
    }
  }

  /**
   * Update existing rights with new attestation
   * @param {string} contentId - ID of the content to update
   * @param {string} attestationUid - New attestation UID
   * @returns {Promise<Object>} Update details
   */
  async updateRightsAttestation(contentId, attestationUid) {
    this._validateInitialized();
    
    try {
      console.log(`[RightsReg] Updating rights attestation for content ID: ${contentId}`);
      
      if (this.mockMode) {
        return this._mockUpdateRights(contentId, attestationUid);
      }
      
      // Submit update transaction
      const tx = await this.rightsVaultContract.updateRightsAttestation(
        contentId,
        attestationUid,
        { gasLimit: 300000 }
      );
      
      console.log(`[RightsReg] Update transaction submitted: ${tx.hash}`);
      
      // Wait for transaction to be mined
      const receipt = await tx.wait();
      console.log(`[RightsReg] Update confirmed in block ${receipt.blockNumber}`);
      
      return {
        contentId: contentId,
        txHash: receipt.transactionHash,
        blockNumber: receipt.blockNumber,
        attestationUid: attestationUid,
        timestamp: Math.floor(Date.now() / 1000)
      };
    } catch (error) {
      console.error('[RightsReg] Error updating rights attestation:', error);
      throw error;
    }
  }

  /**
   * Get rights data from the blockchain
   * @param {string} contentId - ID of the content to retrieve
   * @returns {Promise<Object>} Rights data
   */
  async getRightsData(contentId) {
    this._validateInitialized();
    
    try {
      console.log(`[RightsReg] Retrieving rights data for content ID: ${contentId}`);
      
      if (this.mockMode) {
        return this._mockGetRightsData(contentId);
      }
      
      // Get rights data from contract
      const rightsData = await this.rightsVaultContract.getRightsData(contentId);
      
      // Parse metadata from JSON
      let metadata = {};
      try {
        metadata = JSON.parse(rightsData.metadata);
      } catch (e) {
        console.warn(`[RightsReg] Could not parse metadata for ${contentId}:`, e);
      }
      
      return {
        contentId: contentId,
        isActive: rightsData.isActive,
        ownerAddress: rightsData.owner,
        attestationUid: rightsData.attestationUid,
        registrationTime: rightsData.registrationTime.toNumber(),
        lastUpdateTime: rightsData.lastUpdateTime.toNumber(),
        metadata: metadata
      };
    } catch (error) {
      console.error('[RightsReg] Error retrieving rights data:', error);
      throw error;
    }
  }

  /**
   * Deactivate rights for a specific content ID
   * @param {string} contentId - ID of the content to deactivate
   * @returns {Promise<Object>} Deactivation details
   */
  async deactivateRights(contentId) {
    this._validateInitialized();
    
    try {
      console.log(`[RightsReg] Deactivating rights for content ID: ${contentId}`);
      
      if (this.mockMode) {
        return this._mockDeactivateRights(contentId);
      }
      
      // Submit deactivation transaction
      const tx = await this.rightsVaultContract.deactivateRights(
        contentId,
        { gasLimit: 200000 }
      );
      
      console.log(`[RightsReg] Deactivation transaction submitted: ${tx.hash}`);
      
      // Wait for transaction to be mined
      const receipt = await tx.wait();
      console.log(`[RightsReg] Deactivation confirmed in block ${receipt.blockNumber}`);
      
      return {
        contentId: contentId,
        txHash: receipt.transactionHash,
        blockNumber: receipt.blockNumber,
        deactivated: true,
        timestamp: Math.floor(Date.now() / 1000)
      };
    } catch (error) {
      console.error('[RightsReg] Error deactivating rights:', error);
      throw error;
    }
  }

  /**
   * Generate a deterministic content ID from rights data
   * @param {Object} rightsData - Rights data
   * @returns {string} Generated content ID
   * @private
   */
  _generateContentId(rightsData) {
    try {
      // Create a deterministic identifier from the music content data
      const dataString = `${rightsData.title}|${rightsData.artist}|${rightsData.publisher || ''}|${rightsData.year || ''}`;
      const contentHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes(dataString));
      return contentHash;
    } catch (error) {
      console.error('[RightsReg] Error generating content ID:', error);
      throw error;
    }
  }

  /**
   * Mock register rights (for testing environments)
   * @param {string} ownerAddress - Owner address
   * @param {Object} rightsData - Rights data
   * @param {string} attestationUid - Attestation UID
   * @returns {Promise<Object>} Mock registration details
   * @private
   */
  _mockRegisterRights(ownerAddress, rightsData, attestationUid) {
    // Generate mock content ID
    const contentId = this._generateContentId(rightsData);
    console.log(`[RightsReg] Mock registered rights with content ID: ${contentId}`);
    
    return {
      contentId: contentId,
      txHash: `0x${Array(64).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join('')}`,
      blockNumber: Math.floor(Math.random() * 1000000),
      ownerAddress: ownerAddress,
      attestationUid: attestationUid,
      timestamp: Math.floor(Date.now() / 1000)
    };
  }

  /**
   * Mock update rights (for testing environments)
   * @param {string} contentId - Content ID
   * @param {string} attestationUid - New attestation UID
   * @returns {Promise<Object>} Mock update details
   * @private
   */
  _mockUpdateRights(contentId, attestationUid) {
    console.log(`[RightsReg] Mock updated rights for content ID: ${contentId}`);
    
    return {
      contentId: contentId,
      txHash: `0x${Array(64).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join('')}`,
      blockNumber: Math.floor(Math.random() * 1000000),
      attestationUid: attestationUid,
      timestamp: Math.floor(Date.now() / 1000)
    };
  }

  /**
   * Mock get rights data (for testing environments)
   * @param {string} contentId - Content ID
   * @returns {Promise<Object>} Mock rights data
   * @private
   */
  _mockGetRightsData(contentId) {
    console.log(`[RightsReg] Mock retrieved rights data for content ID: ${contentId}`);
    
    return {
      contentId: contentId,
      isActive: true,
      ownerAddress: '0x1234567890123456789012345678901234567890',
      attestationUid: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
      registrationTime: Math.floor(Date.now() / 1000) - 86400, // One day ago
      lastUpdateTime: Math.floor(Date.now() / 1000) - 3600,    // One hour ago
      metadata: {
        title: 'Mock Song Title',
        artist: 'Mock Artist',
        publisher: 'Mock Publisher',
        year: '2023',
        genre: 'Pop'
      }
    };
  }

  /**
   * Mock deactivate rights (for testing environments)
   * @param {string} contentId - Content ID
   * @returns {Promise<Object>} Mock deactivation details
   * @private
   */
  _mockDeactivateRights(contentId) {
    console.log(`[RightsReg] Mock deactivated rights for content ID: ${contentId}`);
    
    return {
      contentId: contentId,
      txHash: `0x${Array(64).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join('')}`,
      blockNumber: Math.floor(Math.random() * 1000000),
      deactivated: true,
      timestamp: Math.floor(Date.now() / 1000)
    };
  }

  /**
   * Validate that the service is initialized
   * @private
   */
  _validateInitialized() {
    if (!this.initialized) {
      throw new Error('Rights Registration Service not initialized. Call initialize() first.');
    }
  }
}

// Export singleton instance
module.exports = new RightsRegistrationService(); 