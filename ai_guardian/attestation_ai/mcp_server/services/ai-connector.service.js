/**
 * AI Connector Service
 * 
 * This service handles communication with AI analysis systems for
 * music content verification.
 */

const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');
const config = require('../config');

class AIConnectorService {
  constructor() {
    this.initialized = false;
    this.apiBaseUrl = '';
    this.apiKey = '';
    this.mockMode = process.env.NODE_ENV === 'test' || process.env.MOCK_AI === 'true';
  }

  /**
   * Initialize the AI connector service
   * @returns {Promise<boolean>} Initialization success status
   */
  async initialize() {
    try {
      console.log('[AI Connector] Initializing AI connector service...');
      
      if (this.mockMode) {
        console.log('[AI Connector] Running in mock mode - using simulated AI responses');
        this.initialized = true;
        return true;
      }
      
      // Set up API credentials from config
      this.apiBaseUrl = config.ai.apiBaseUrl;
      this.apiKey = config.ai.apiKey;
      
      // Validate credentials
      if (!this.apiBaseUrl || !this.apiKey) {
        throw new Error('AI API credentials not configured');
      }
      
      // Test connection to API
      await this._testConnection();
      
      this.initialized = true;
      console.log('[AI Connector] AI connector service initialized successfully');
      return true;
    } catch (error) {
      console.error('[AI Connector] Error initializing AI connector service:', error);
      throw error;
    }
  }

  /**
   * Submit audio content for AI analysis
   * @param {Object} data - Content data
   * @param {string} data.filePath - Path to audio file
   * @param {Object} metadata - Track metadata
   * @returns {Promise<Object>} Verification request result
   */
  async submitVerificationRequest(data, metadata) {
    this._validateInitialized();
    
    try {
      console.log('[AI Connector] Submitting verification request for:', metadata.trackTitle);
      
      if (this.mockMode) {
        return this._mockSubmitVerification(data, metadata);
      }
      
      const form = new FormData();
      
      // Add audio file to form
      form.append('audio', fs.createReadStream(data.filePath));
      
      // Add metadata to form
      form.append('metadata', JSON.stringify({
        trackId: metadata.trackId,
        trackTitle: metadata.trackTitle,
        artist: metadata.artist,
        publisher: metadata.publisher,
        isrc: metadata.isrc,
        upc: metadata.upc,
        duration: metadata.duration,
      }));
      
      // Submit to AI API
      const response = await axios.post(
        `${this.apiBaseUrl}/verify`, 
        form,
        {
          headers: {
            ...form.getHeaders(),
            'Authorization': `Bearer ${this.apiKey}`,
          },
          timeout: 30000, // 30 seconds
        }
      );
      
      if (response.status !== 202) {
        throw new Error(`Unexpected response status: ${response.status}`);
      }
      
      const requestId = response.data.requestId;
      console.log(`[AI Connector] Verification request submitted, ID: ${requestId}`);
      
      return {
        requestId,
        status: 'PENDING',
        submittedAt: new Date().toISOString(),
      };
    } catch (error) {
      console.error('[AI Connector] Error submitting verification request:', error);
      throw error;
    }
  }

  /**
   * Check the status of a verification request
   * @param {string} requestId - Verification request ID
   * @returns {Promise<Object>} Verification request status
   */
  async checkVerificationStatus(requestId) {
    this._validateInitialized();
    
    try {
      console.log(`[AI Connector] Checking verification status for request: ${requestId}`);
      
      if (this.mockMode) {
        return this._mockCheckStatus(requestId);
      }
      
      // Call AI API to get status
      const response = await axios.get(
        `${this.apiBaseUrl}/verify/status/${requestId}`,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
          },
          timeout: 15000, // 15 seconds
        }
      );
      
      return {
        requestId,
        status: response.data.status,
        result: response.data.result,
        updatedAt: new Date().toISOString(),
      };
    } catch (error) {
      console.error('[AI Connector] Error checking verification status:', error);
      throw error;
    }
  }

  /**
   * Get the detailed results of a completed verification
   * @param {string} requestId - Verification request ID
   * @returns {Promise<Object>} Verification results
   */
  async getVerificationResults(requestId) {
    this._validateInitialized();
    
    try {
      console.log(`[AI Connector] Getting verification results for request: ${requestId}`);
      
      if (this.mockMode) {
        return this._mockGetResults(requestId);
      }
      
      // Call AI API to get results
      const response = await axios.get(
        `${this.apiBaseUrl}/verify/results/${requestId}`,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
          },
          timeout: 15000, // 15 seconds
        }
      );
      
      if (response.data.status !== 'COMPLETED') {
        throw new Error(`Verification not yet completed: ${response.data.status}`);
      }
      
      return response.data.results;
    } catch (error) {
      console.error('[AI Connector] Error getting verification results:', error);
      throw error;
    }
  }

  /**
   * Test connection to the AI API
   * @private
   */
  async _testConnection() {
    try {
      const response = await axios.get(
        `${this.apiBaseUrl}/health`,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
          },
          timeout: 10000, // 10 seconds
        }
      );
      
      if (response.status !== 200 || response.data.status !== 'ok') {
        throw new Error(`AI API health check failed: ${response.status}`);
      }
      
      console.log('[AI Connector] Connection to AI API verified');
    } catch (error) {
      console.error('[AI Connector] AI API connection test failed:', error);
      throw new Error('Could not connect to AI API. Check credentials and network.');
    }
  }

  /**
   * Mock submission of verification request for testing
   * @param {Object} data - Content data
   * @param {Object} metadata - Track metadata
   * @returns {Promise<Object>} Mock verification request result
   * @private
   */
  async _mockSubmitVerification(data, metadata) {
    console.log('[AI Connector] Creating mock verification request');
    
    // Generate a mock request ID
    const requestId = `req_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
    
    return {
      requestId,
      status: 'PENDING',
      submittedAt: new Date().toISOString(),
      metadata: {
        ...metadata,
        mockRequest: true
      }
    };
  }

  /**
   * Mock checking status of verification request for testing
   * @param {string} requestId - Verification request ID
   * @returns {Promise<Object>} Mock verification request status
   * @private
   */
  async _mockCheckStatus(requestId) {
    console.log(`[AI Connector] Checking mock verification status: ${requestId}`);
    
    // Simulate processing delays based on request ID
    const requestTimestamp = parseInt(requestId.split('_')[1], 10) || Date.now();
    const elapsedMs = Date.now() - requestTimestamp;
    
    // Set different statuses based on elapsed time
    let status = 'PENDING';
    if (elapsedMs > 5000) status = 'PROCESSING';
    if (elapsedMs > 10000) status = 'COMPLETED';
    
    return {
      requestId,
      status,
      progress: Math.min(100, Math.floor(elapsedMs / 100)),
      updatedAt: new Date().toISOString()
    };
  }

  /**
   * Mock getting results of verification request for testing
   * @param {string} requestId - Verification request ID
   * @returns {Promise<Object>} Mock verification results
   * @private
   */
  async _mockGetResults(requestId) {
    console.log(`[AI Connector] Getting mock verification results: ${requestId}`);
    
    // Generate consistent deterministic results based on requestId
    const lastDigit = requestId.charAt(requestId.length - 1);
    const numValue = parseInt(lastDigit, 10) || 5;
    
    // Confidence score based on last digit of request ID (for testing different scenarios)
    const confidenceScore = Math.min(98, 75 + (numValue * 2));
    const plagiarismDetected = numValue < 3; // 30% chance of plagiarism for testing
    
    return {
      requestId,
      status: 'COMPLETED',
      completedAt: new Date().toISOString(),
      results: {
        verified: confidenceScore > 80 && !plagiarismDetected,
        confidenceScore,
        analysis: {
          originalityScore: plagiarismDetected ? 35 + numValue * 5 : 85 + numValue,
          plagiarismDetected,
          similarWorks: plagiarismDetected ? [
            {
              title: 'Similar Track Example',
              artist: 'Another Artist',
              similarity: 0.7 + (numValue * 0.03),
              sections: [
                { start: '0:15', end: '0:45', similarity: 0.85 },
                { start: '1:30', end: '2:15', similarity: 0.92 }
              ]
            }
          ] : [],
          verification: {
            metadataMatches: true,
            audioFingerprint: {
              matches: confidenceScore > 90,
              confidence: confidenceScore / 100
            },
            contentProfile: {
              tempo: 120 + numValue,
              key: ['C', 'G', 'D', 'A', 'E'][numValue % 5] + ['maj', 'min'][numValue % 2],
              genre: ['Pop', 'Rock', 'Electronic', 'Hip-Hop', 'Jazz'][numValue % 5]
            }
          }
        }
      }
    };
  }

  /**
   * Validate that the service is initialized
   * @private
   */
  _validateInitialized() {
    if (!this.initialized) {
      throw new Error('AI connector service not initialized. Call initialize() first.');
    }
  }
}

// Export singleton instance
module.exports = new AIConnectorService(); 