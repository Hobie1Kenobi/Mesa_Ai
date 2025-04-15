/**
 * Music Content Protection (MCP) Service
 * 
 * This service coordinates the verification of music content through AI analysis
 * and blockchain attestation, serving as the core of the MESA AI Guardian system.
 */

const aiConnector = require('./ai-connector.service');
const easService = require('./eas.service');
const rightsRegistration = require('./rights-registration.service');
const config = require('../config');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const EventEmitter = require('events');

class MCPService extends EventEmitter {
  constructor() {
    super();
    this.initialized = false;
    this.processingJobs = new Map();
    this.workDirectory = '';
    this.mockMode = process.env.NODE_ENV === 'test' || process.env.MOCK_MCP === 'true';
  }

  /**
   * Initialize the MCP service and all required sub-services
   * @returns {Promise<boolean>} Initialization success status
   */
  async initialize() {
    try {
      console.log('[MCP] Initializing Music Content Protection service...');
      
      // Set up the working directory
      this.workDirectory = process.env.WORK_DIR || path.join(__dirname, '../work');
      await this._ensureDirectory(this.workDirectory);
      
      // Initialize required services
      await aiConnector.initialize();
      await easService.initialize();
      
      // Attempt to initialize rights registration service
      try {
        await rightsRegistration.initialize();
      } catch (err) {
        console.warn('[MCP] Rights registration service failed to initialize. Some features may be limited:', err.message);
      }
      
      this.initialized = true;
      console.log('[MCP] Music Content Protection service initialized successfully');
      
      return true;
    } catch (error) {
      console.error('[MCP] Error initializing MCP service:', error);
      throw error;
    }
  }

  /**
   * Submit content for protection
   * @param {Object} contentData - Content information
   * @param {string} contentData.filePath - Path to audio file
   * @param {Object} metadata - Track metadata
   * @param {string} ownerAddress - Blockchain address of content owner
   * @returns {Promise<Object>} Job receipt with ID
   */
  async submitProtectionRequest(contentData, metadata, ownerAddress) {
    this._validateInitialized();
    
    try {
      console.log(`[MCP] Submitting protection request for: ${metadata.trackTitle} by ${metadata.artist}`);
      
      // Create a job ID
      const jobId = `job_${Date.now()}_${uuidv4().substring(0, 8)}`;
      
      // Create a job object to track progress
      const job = {
        id: jobId,
        status: 'SUBMITTED',
        contentData,
        metadata,
        ownerAddress,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        steps: {
          verification: { status: 'PENDING', requestId: null, results: null },
          attestation: { status: 'PENDING', txHash: null, attestationUID: null },
          registration: { status: 'PENDING', txHash: null, tokenId: null }
        },
        errors: []
      };
      
      // Store job information
      this.processingJobs.set(jobId, job);
      
      // Start processing asynchronously
      setTimeout(() => this._processJob(jobId), 100);
      
      return {
        jobId,
        status: job.status,
        createdAt: job.createdAt,
        metadata: {
          trackId: metadata.trackId,
          trackTitle: metadata.trackTitle,
          artist: metadata.artist
        }
      };
    } catch (error) {
      console.error('[MCP] Error submitting protection request:', error);
      throw error;
    }
  }

  /**
   * Get the status of a protection job
   * @param {string} jobId - Job ID to check
   * @returns {Promise<Object>} Current job status
   */
  async getJobStatus(jobId) {
    this._validateInitialized();
    
    try {
      console.log(`[MCP] Getting status for job: ${jobId}`);
      
      const job = this.processingJobs.get(jobId);
      
      if (!job) {
        throw new Error(`Job not found: ${jobId}`);
      }
      
      return {
        jobId: job.id,
        status: job.status,
        createdAt: job.createdAt,
        updatedAt: job.updatedAt,
        steps: {
          verification: {
            status: job.steps.verification.status,
            completed: job.steps.verification.status === 'COMPLETED',
            verified: job.steps.verification.results?.verified || false,
          },
          attestation: {
            status: job.steps.attestation.status,
            completed: job.steps.attestation.status === 'COMPLETED',
            attestationUID: job.steps.attestation.attestationUID,
          },
          registration: {
            status: job.steps.registration.status,
            completed: job.steps.registration.status === 'COMPLETED',
            tokenId: job.steps.registration.tokenId,
          }
        },
        errors: job.errors
      };
    } catch (error) {
      console.error('[MCP] Error getting job status:', error);
      throw error;
    }
  }

  /**
   * Get detailed results for a completed job
   * @param {string} jobId - Job ID to get results for
   * @returns {Promise<Object>} Detailed job results
   */
  async getJobResults(jobId) {
    this._validateInitialized();
    
    try {
      console.log(`[MCP] Getting results for job: ${jobId}`);
      
      const job = this.processingJobs.get(jobId);
      
      if (!job) {
        throw new Error(`Job not found: ${jobId}`);
      }
      
      if (job.status !== 'COMPLETED' && job.status !== 'PARTIALLY_COMPLETED' && job.status !== 'FAILED') {
        throw new Error(`Job not completed: ${job.status}`);
      }
      
      return {
        jobId: job.id,
        status: job.status,
        createdAt: job.createdAt,
        completedAt: job.completedAt,
        metadata: {
          trackId: job.metadata.trackId,
          trackTitle: job.metadata.trackTitle,
          artist: job.metadata.artist,
          publisher: job.metadata.publisher,
          isrc: job.metadata.isrc,
          upc: job.metadata.upc
        },
        verification: job.steps.verification.results,
        attestation: {
          successful: job.steps.attestation.status === 'COMPLETED',
          attestationUID: job.steps.attestation.attestationUID,
          txHash: job.steps.attestation.txHash,
          attestationData: job.steps.attestation.data
        },
        registration: {
          successful: job.steps.registration.status === 'COMPLETED',
          tokenId: job.steps.registration.tokenId,
          txHash: job.steps.registration.txHash,
          tokenURI: job.steps.registration.tokenURI
        },
        errors: job.errors
      };
    } catch (error) {
      console.error('[MCP] Error getting job results:', error);
      throw error;
    }
  }

  /**
   * Process a protection job asynchronously
   * @param {string} jobId - Job ID to process
   * @private
   */
  async _processJob(jobId) {
    const job = this.processingJobs.get(jobId);
    
    if (!job) {
      console.error(`[MCP] Job not found for processing: ${jobId}`);
      return;
    }
    
    try {
      console.log(`[MCP] Processing job: ${jobId}`);
      
      // Update job status
      job.status = 'PROCESSING';
      job.updatedAt = new Date().toISOString();
      
      // Step 1: Submit for AI verification
      try {
        console.log(`[MCP] Submitting for AI verification: ${jobId}`);
        job.steps.verification.status = 'PROCESSING';
        
        // Submit to AI verification service
        const verificationRequest = await aiConnector.submitVerificationRequest(
          job.contentData, 
          job.metadata
        );
        
        job.steps.verification.requestId = verificationRequest.requestId;
        job.updatedAt = new Date().toISOString();
        
        // Wait for verification to complete
        await this._waitForVerification(jobId);
        
      } catch (error) {
        console.error(`[MCP] Error in verification step: ${error.message}`);
        job.steps.verification.status = 'FAILED';
        job.errors.push({
          step: 'verification',
          message: error.message,
          timestamp: new Date().toISOString()
        });
      }
      
      // Don't proceed if verification failed or content is not verified
      if (job.steps.verification.status !== 'COMPLETED' || 
          !job.steps.verification.results?.verified) {
        
        if (job.steps.verification.status === 'COMPLETED' && !job.steps.verification.results?.verified) {
          job.errors.push({
            step: 'verification',
            message: 'Content failed verification check',
            timestamp: new Date().toISOString()
          });
        }
        
        job.status = 'FAILED';
        job.completedAt = new Date().toISOString();
        job.updatedAt = job.completedAt;
        
        this.emit('job:failed', { jobId, reason: 'Verification failed or content not verified' });
        return;
      }
      
      // Step 2: Create blockchain attestation
      try {
        console.log(`[MCP] Creating blockchain attestation: ${jobId}`);
        job.steps.attestation.status = 'PROCESSING';
        job.updatedAt = new Date().toISOString();
        
        // Format data for attestation
        const attestationData = {
          contentId: job.metadata.trackId,
          title: job.metadata.trackTitle,
          artist: job.metadata.artist,
          publisher: job.metadata.publisher,
          isrc: job.metadata.isrc || '',
          upc: job.metadata.upc || '',
          verificationScore: job.steps.verification.results.confidenceScore,
          verificationTimestamp: Date.now(),
          fingerprint: job.steps.verification.results.analysis?.contentProfile || {}
        };
        
        // Create attestation on blockchain
        const attestation = await easService.createAttestation(
          job.ownerAddress,
          attestationData
        );
        
        job.steps.attestation.status = 'COMPLETED';
        job.steps.attestation.attestationUID = attestation.uid;
        job.steps.attestation.txHash = attestation.txHash;
        job.steps.attestation.data = attestationData;
        job.updatedAt = new Date().toISOString();
        
      } catch (error) {
        console.error(`[MCP] Error in attestation step: ${error.message}`);
        job.steps.attestation.status = 'FAILED';
        job.errors.push({
          step: 'attestation',
          message: error.message,
          timestamp: new Date().toISOString()
        });
      }
      
      // Step 3: Register rights token (if rights registration is available)
      try {
        if (rightsRegistration.initialized) {
          console.log(`[MCP] Registering rights token: ${jobId}`);
          job.steps.registration.status = 'PROCESSING';
          job.updatedAt = new Date().toISOString();
          
          // Prepare metadata for token
          const tokenMetadata = {
            name: `${job.metadata.trackTitle} - ${job.metadata.artist}`,
            description: `Music rights for "${job.metadata.trackTitle}" by ${job.metadata.artist}`,
            external_url: '',
            image: '', // Would typically be album art
            properties: {
              trackId: job.metadata.trackId,
              trackTitle: job.metadata.trackTitle,
              artist: job.metadata.artist,
              publisher: job.metadata.publisher,
              isrc: job.metadata.isrc || '',
              upc: job.metadata.upc || '',
              attestationUID: job.steps.attestation.attestationUID,
              verificationScore: job.steps.verification.results.confidenceScore
            }
          };
          
          // Register rights token
          const registration = await rightsRegistration.registerRights(
            job.ownerAddress,
            tokenMetadata,
            job.steps.attestation.attestationUID
          );
          
          job.steps.registration.status = 'COMPLETED';
          job.steps.registration.tokenId = registration.tokenId;
          job.steps.registration.txHash = registration.txHash;
          job.steps.registration.tokenURI = registration.tokenURI;
          
        } else {
          console.log(`[MCP] Skipping rights registration (service not available): ${jobId}`);
          job.steps.registration.status = 'SKIPPED';
        }
      } catch (error) {
        console.error(`[MCP] Error in registration step: ${error.message}`);
        job.steps.registration.status = 'FAILED';
        job.errors.push({
          step: 'registration',
          message: error.message,
          timestamp: new Date().toISOString()
        });
      }
      
      // Determine final status
      const allCompleted = 
        job.steps.verification.status === 'COMPLETED' &&
        job.steps.attestation.status === 'COMPLETED' &&
        (job.steps.registration.status === 'COMPLETED' || job.steps.registration.status === 'SKIPPED');
      
      const allFailed = 
        job.steps.verification.status === 'FAILED' &&
        job.steps.attestation.status === 'FAILED' &&
        (job.steps.registration.status === 'FAILED' || job.steps.registration.status === 'SKIPPED');
      
      if (allCompleted) {
        job.status = 'COMPLETED';
      } else if (allFailed) {
        job.status = 'FAILED';
      } else {
        job.status = 'PARTIALLY_COMPLETED';
      }
      
      job.completedAt = new Date().toISOString();
      job.updatedAt = job.completedAt;
      
      // Emit appropriate event
      this.emit(`job:${job.status.toLowerCase()}`, { jobId });
      
      console.log(`[MCP] Job completed with status ${job.status}: ${jobId}`);
      
    } catch (error) {
      console.error(`[MCP] Unhandled error processing job: ${jobId}`, error);
      
      // Update job with error status
      job.status = 'FAILED';
      job.completedAt = new Date().toISOString();
      job.updatedAt = job.completedAt;
      job.errors.push({
        step: 'processing',
        message: `Unhandled error: ${error.message}`,
        timestamp: new Date().toISOString()
      });
      
      this.emit('job:failed', { jobId, reason: 'Unhandled error' });
    }
  }

  /**
   * Wait for verification to complete
   * @param {string} jobId - Job ID to check
   * @private
   */
  async _waitForVerification(jobId) {
    const job = this.processingJobs.get(jobId);
    if (!job) return;
    
    const requestId = job.steps.verification.requestId;
    if (!requestId) {
      throw new Error('No verification request ID');
    }
    
    // Try up to 10 times with increasing delays
    const maxAttempts = 10;
    const baseDelay = 2000; // 2 seconds base delay
    
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      // Calculate exponential backoff delay
      const delay = baseDelay * Math.pow(1.5, attempt);
      
      // Wait before checking
      await new Promise(resolve => setTimeout(resolve, delay));
      
      try {
        // Check verification status
        const status = await aiConnector.checkVerificationStatus(requestId);
        
        if (status.status === 'COMPLETED') {
          // Get full results
          const results = await aiConnector.getVerificationResults(requestId);
          
          // Update job with results
          job.steps.verification.status = 'COMPLETED';
          job.steps.verification.results = results;
          job.updatedAt = new Date().toISOString();
          
          console.log(`[MCP] Verification completed for job: ${jobId}`);
          return;
        } else if (status.status === 'FAILED') {
          throw new Error('Verification failed');
        }
        
        // Log progress
        console.log(`[MCP] Verification in progress for job: ${jobId}, Status: ${status.status}, Attempt: ${attempt + 1}/${maxAttempts}`);
        
      } catch (error) {
        console.error(`[MCP] Error checking verification status: ${error.message}`);
        
        // On the last attempt, throw the error
        if (attempt === maxAttempts - 1) {
          throw error;
        }
      }
    }
    
    // If we get here, verification timed out
    throw new Error('Verification timed out');
  }

  /**
   * Ensure a directory exists
   * @param {string} dir - Directory path
   * @private
   */
  async _ensureDirectory(dir) {
    try {
      await fs.promises.mkdir(dir, { recursive: true });
    } catch (error) {
      console.error(`[MCP] Error creating directory ${dir}:`, error);
      throw error;
    }
  }

  /**
   * Validate that the service is initialized
   * @private
   */
  _validateInitialized() {
    if (!this.initialized) {
      throw new Error('MCP service not initialized. Call initialize() first.');
    }
  }
}

// Export singleton instance
module.exports = new MCPService(); 