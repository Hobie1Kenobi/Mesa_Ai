/**
 * AI Analyzer Service
 * 
 * This service handles AI-based analysis of music content including:
 * - Fingerprinting audio files
 * - Analyzing similarity against existing catalogs
 * - Generating metadata for attestations
 * - Integrating with EAS for on-chain attestations
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const crypto = require('crypto');
const { promisify } = require('util');
const easService = require('./eas.service');
const config = require('../config');
const logger = require('../utils/logger');

// Convert fs functions to promise-based
const mkdir = promisify(fs.mkdir);
const writeFile = promisify(fs.writeFile);
const readFile = promisify(fs.readFile);
const unlink = promisify(fs.unlink);
const access = promisify(fs.access);

class AIAnalyzerService {
  constructor() {
    this.initialized = false;
    this.analysisQueue = [];
    this.isProcessing = false;
    this.tempDir = path.join(__dirname, '../temp');
    this.knownFingerprints = new Map(); // In-memory cache of fingerprints for demo
  }

  /**
   * Initialize the AI Analyzer service
   * @returns {Promise<boolean>} - Success status
   */
  async initialize() {
    try {
      logger.info('Initializing AI Analyzer Service');
      
      // Create temp directory if it doesn't exist
      if (!fs.existsSync(this.tempDir)) {
        await mkdir(this.tempDir, { recursive: true });
      }
      
      // Initialize the EAS service
      await easService.initialize();
      
      this.initialized = true;
      logger.info('AI Analyzer Service initialized successfully');
      
      // Start processing the queue
      this._startProcessingQueue();
      
      return true;
    } catch (error) {
      logger.error('Failed to initialize AI Analyzer Service', { error: error.message, stack: error.stack });
      throw new Error(`Failed to initialize AI Analyzer Service: ${error.message}`);
    }
  }

  /**
   * Analyze content for originality and create attestation
   * 
   * @param {string} contentId - Unique identifier for the content
   * @param {string} contentURI - URI pointing to the content (HTTP, IPFS, or local path)
   * @param {Object} metadata - Additional metadata about the content
   * @returns {Promise<Object>} - Analysis request data with status
   */
  async analyzeContent(contentId, contentURI, metadata) {
    if (!this.initialized) {
      await this.initialize();
    }
    
    try {
      logger.info('Queueing content for analysis', { contentId, contentURI });
      
      // Validate inputs
      if (!contentId || !contentURI) {
        throw new Error('Content ID and URI are required');
      }
      
      // Create an analysis request
      const analysisRequest = {
        contentId,
        contentURI,
        metadata: metadata || {},
        status: 'queued',
        queuedAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      // Add to queue
      this.analysisQueue.push(analysisRequest);
      
      // Start processing if not already
      if (!this.isProcessing) {
        this._startProcessingQueue();
      }
      
      return analysisRequest;
    } catch (error) {
      logger.error('Failed to queue content for analysis', { error: error.message, contentId });
      throw new Error(`Failed to queue content for analysis: ${error.message}`);
    }
  }

  /**
   * Start processing the analysis queue
   * @private
   */
  _startProcessingQueue() {
    if (this.isProcessing || this.analysisQueue.length === 0) {
      return;
    }
    
    this.isProcessing = true;
    
    // Process items sequentially
    const processNext = async () => {
      if (this.analysisQueue.length === 0) {
        this.isProcessing = false;
        return;
      }
      
      const item = this.analysisQueue.shift();
      try {
        await this._processContentItem(item);
      } catch (error) {
        logger.error('Error processing queue item', { 
          error: error.message, 
          contentId: item.contentId 
        });
        
        // Update item status to failed
        item.status = 'failed';
        item.error = error.message;
        item.updatedAt = new Date().toISOString();
      }
      
      // Process next item
      setTimeout(processNext, 100);
    };
    
    // Start processing
    processNext();
  }

  /**
   * Process a single content item
   * @param {Object} item - The queue item to process
   * @private
   */
  async _processContentItem(item) {
    try {
      logger.info('Processing content item', { contentId: item.contentId, status: 'processing' });
      
      // Update status
      item.status = 'processing';
      item.updatedAt = new Date().toISOString();
      
      // Download content
      logger.info('Downloading content', { contentId: item.contentId, contentURI: item.contentURI });
      const contentPath = await this._downloadContent(item.contentURI, item.contentId);
      
      // Generate fingerprint
      logger.info('Generating audio fingerprint', { contentId: item.contentId });
      const fingerprint = await this._generateFingerprint(contentPath, item.contentId);
      
      // Check similarity against known content
      logger.info('Checking similarity', { contentId: item.contentId });
      const similarityResults = await this._checkSimilarity(fingerprint, item.contentId);
      
      // Analyze results and determine originality
      logger.info('Analyzing similarity results', { contentId: item.contentId });
      const analysisResults = await this._analyzeResults(similarityResults, item.metadata, item.contentId);
      
      // Prepare data for attestation
      const attestationData = {
        contentId: item.contentId,
        title: item.metadata.title || `Content ${item.contentId}`,
        artist: item.metadata.artist || 'Unknown Artist',
        publisher: item.metadata.publisher || 'Unknown Publisher',
        creationYear: parseInt(item.metadata.creationYear) || new Date().getFullYear(),
        metadataURI: item.metadata.metadataURI || '',
        isOriginal: analysisResults.isOriginal
      };
      
      // Create attestation
      logger.info('Creating attestation', { contentId: item.contentId, isOriginal: analysisResults.isOriginal });
      const attestation = await easService.createAttestation(attestationData);
      
      // Clean up temporary files
      await this._cleanup(contentPath);
      
      // Update item with results
      item.status = 'completed';
      item.analysisResults = analysisResults;
      item.attestation = attestation;
      item.updatedAt = new Date().toISOString();
      item.completedAt = new Date().toISOString();
      
      logger.info('Content analysis completed', { 
        contentId: item.contentId, 
        status: 'completed',
        isOriginal: analysisResults.isOriginal,
        attestationUID: attestation.attestationUID
      });
      
      return item;
    } catch (error) {
      logger.error('Failed to process content item', { error: error.message, contentId: item.contentId });
      
      // Update item status
      item.status = 'failed';
      item.error = error.message;
      item.updatedAt = new Date().toISOString();
      
      throw error;
    }
  }

  /**
   * Download content from URI
   * @param {string} contentURI - URI pointing to the content
   * @param {string} contentId - Unique identifier for the content
   * @returns {Promise<string>} - Path to downloaded content
   * @private
   */
  async _downloadContent(contentURI, contentId) {
    try {
      const fileExtension = this._getFileExtension(contentURI);
      const tempFilePath = path.join(this.tempDir, `${contentId}${fileExtension}`);
      
      // Check if URI is a local file path
      if (contentURI.startsWith('/') || contentURI.includes(':\\')) {
        // Check if file exists
        if (await this._fileExists(contentURI)) {
          // For local files, read and write to temp directory
          const data = await readFile(contentURI);
          await writeFile(tempFilePath, data);
          return tempFilePath;
        } else {
          throw new Error(`Local file not found: ${contentURI}`);
        }
      }
      
      // Handle HTTP/HTTPS URIs
      if (contentURI.startsWith('http://') || contentURI.startsWith('https://')) {
        const response = await axios({
          method: 'GET',
          url: contentURI,
          responseType: 'arraybuffer'
        });
        
        await writeFile(tempFilePath, response.data);
        return tempFilePath;
      }
      
      // Handle IPFS URIs
      if (contentURI.startsWith('ipfs://')) {
        const ipfsHash = contentURI.replace('ipfs://', '');
        const ipfsGateway = config.ipfs?.gateway || 'https://ipfs.io/ipfs/';
        const ipfsUrl = `${ipfsGateway}${ipfsHash}`;
        
        const response = await axios({
          method: 'GET',
          url: ipfsUrl,
          responseType: 'arraybuffer'
        });
        
        await writeFile(tempFilePath, response.data);
        return tempFilePath;
      }
      
      throw new Error(`Unsupported URI format: ${contentURI}`);
    } catch (error) {
      logger.error('Failed to download content', { error: error.message, contentURI, contentId });
      throw new Error(`Failed to download content: ${error.message}`);
    }
  }

  /**
   * Generate audio fingerprint
   * @param {string} contentPath - Path to the content file
   * @param {string} contentId - Unique identifier for the content
   * @returns {Promise<Object>} - Fingerprint data
   * @private
   */
  async _generateFingerprint(contentPath, contentId) {
    try {
      // In development/test mode, generate a mock fingerprint
      if (config.env === 'development' || config.env === 'test') {
        return this._generateMockFingerprint(contentPath, contentId);
      }
      
      // In a real implementation, this would use a proper audio fingerprinting library
      // For example, using a library like Chromaprint/AcoustID
      throw new Error('Real fingerprinting not implemented - use dev/test environment');
    } catch (error) {
      logger.error('Failed to generate fingerprint', { error: error.message, contentId });
      throw new Error(`Failed to generate fingerprint: ${error.message}`);
    }
  }

  /**
   * Check similarity against known content
   * @param {Object} fingerprint - The fingerprint to check
   * @param {string} contentId - Unique identifier for the content
   * @returns {Promise<Array>} - Array of similarity matches
   * @private
   */
  async _checkSimilarity(fingerprint, contentId) {
    try {
      // In development/test mode, generate mock similarity results
      if (config.env === 'development' || config.env === 'test') {
        return this._generateMockSimilarityResults(fingerprint, contentId);
      }
      
      // In a real implementation, this would query a database of fingerprints
      // and use appropriate similarity algorithms
      throw new Error('Real similarity checking not implemented - use dev/test environment');
    } catch (error) {
      logger.error('Failed to check similarity', { error: error.message, contentId });
      throw new Error(`Failed to check similarity: ${error.message}`);
    }
  }

  /**
   * Analyze similarity results to determine originality
   * @param {Array} similarityResults - Results from similarity check
   * @param {Object} metadata - Content metadata
   * @param {string} contentId - Unique identifier for the content
   * @returns {Promise<Object>} - Analysis results
   * @private
   */
  async _analyzeResults(similarityResults, metadata, contentId) {
    try {
      // Find the highest similarity match
      let highestSimilarity = 0;
      let matchingContent = null;
      
      for (const result of similarityResults) {
        if (result.similarity > highestSimilarity) {
          highestSimilarity = result.similarity;
          matchingContent = result;
        }
      }
      
      // Determine if original based on similarity threshold
      const similarityThreshold = config.analyzer?.similarityThreshold || 0.8;
      const isOriginal = highestSimilarity < similarityThreshold;
      
      return {
        isOriginal,
        similarityScore: highestSimilarity,
        matchingContent: matchingContent ? {
          contentId: matchingContent.contentId,
          title: matchingContent.metadata?.title || 'Unknown',
          artist: matchingContent.metadata?.artist || 'Unknown',
          similarity: matchingContent.similarity
        } : null,
        analysisDetails: {
          totalComparisons: similarityResults.length,
          threshold: similarityThreshold,
          analyzedAt: new Date().toISOString()
        }
      };
    } catch (error) {
      logger.error('Failed to analyze results', { error: error.message, contentId });
      throw new Error(`Failed to analyze results: ${error.message}`);
    }
  }

  /**
   * Clean up temporary files
   * @param {string} contentPath - Path to the content file
   * @private
   */
  async _cleanup(contentPath) {
    try {
      if (await this._fileExists(contentPath)) {
        await unlink(contentPath);
      }
    } catch (error) {
      logger.warn('Failed to clean up temporary file', { error: error.message, path: contentPath });
      // Non-critical error, continue
    }
  }

  /**
   * Check if a file exists
   * @param {string} filePath - Path to the file
   * @returns {Promise<boolean>} - Whether the file exists
   * @private
   */
  async _fileExists(filePath) {
    try {
      await access(filePath, fs.constants.F_OK);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get file extension from URI
   * @param {string} uri - The URI
   * @returns {string} - The file extension
   * @private
   */
  _getFileExtension(uri) {
    // Extract the filename from the URI
    let filename;
    if (uri.includes('?')) {
      // Remove query parameters
      uri = uri.split('?')[0];
    }
    
    if (uri.includes('/')) {
      // Extract filename from path
      filename = uri.split('/').pop();
    } else {
      filename = uri;
    }
    
    // Get the extension
    const extMatch = filename.match(/\.[0-9a-z]+$/i);
    if (extMatch) {
      return extMatch[0];
    }
    
    // Default to .bin if no extension found
    return '.bin';
  }

  /**
   * Generate mock fingerprint for testing
   * @param {string} contentPath - Path to the content file
   * @param {string} contentId - Unique identifier for the content
   * @returns {Promise<Object>} - Mock fingerprint data
   * @private
   */
  async _generateMockFingerprint(contentPath, contentId) {
    try {
      // Read file for mock fingerprint (if it exists)
      let fileBuffer;
      if (await this._fileExists(contentPath)) {
        fileBuffer = await readFile(contentPath);
      } else {
        // If file doesn't exist, use contentId as data
        fileBuffer = Buffer.from(contentId);
      }
      
      // Create hash from file content
      const hash = crypto.createHash('sha256').update(fileBuffer).digest('hex');
      
      // Create mock fingerprint data points (for audio, these would be spectral features)
      const dataPoints = [];
      for (let i = 0; i < 10; i++) {
        const segment = hash.substring(i * 6, (i + 1) * 6);
        const value = parseInt(segment, 16) / Math.pow(16, 6);
        dataPoints.push({
          time: i * 0.5, // Time in seconds
          frequency: 100 + Math.floor(value * 1000), // Frequency in Hz
          magnitude: value
        });
      }
      
      const fingerprint = {
        hash,
        dataPoints,
        contentId,
        timestamp: new Date().toISOString()
      };
      
      // Store in in-memory cache for similarity checking
      this.knownFingerprints.set(contentId, {
        fingerprint,
        metadata: {
          contentId,
          title: `Content ${contentId}`,
          artist: 'Test Artist',
          creationYear: 2023
        }
      });
      
      return fingerprint;
    } catch (error) {
      logger.error('Failed to generate mock fingerprint', { error: error.message, contentId });
      throw new Error(`Failed to generate mock fingerprint: ${error.message}`);
    }
  }

  /**
   * Generate mock similarity results for testing
   * @param {Object} fingerprint - The fingerprint to check
   * @param {string} contentId - Unique identifier for the content
   * @returns {Promise<Array>} - Mock similarity results
   * @private
   */
  async _generateMockSimilarityResults(fingerprint, contentId) {
    try {
      const results = [];
      
      // Check against known fingerprints in memory cache
      for (const [knownId, data] of this.knownFingerprints.entries()) {
        // Skip comparing to self
        if (knownId === contentId) {
          continue;
        }
        
        // Calculate mock similarity based on hash comparison
        const knownHash = data.fingerprint.hash;
        const currentHash = fingerprint.hash;
        
        let matchingChars = 0;
        const minLength = Math.min(knownHash.length, currentHash.length);
        
        for (let i = 0; i < minLength; i++) {
          if (knownHash[i] === currentHash[i]) {
            matchingChars++;
          }
        }
        
        // Calculate similarity score (0-1)
        const similarity = matchingChars / minLength;
        
        // If similarity is above 0.1, add to results
        if (similarity > 0.1) {
          results.push({
            contentId: knownId,
            similarity,
            metadata: data.metadata
          });
        }
      }
      
      // Add random similar items if there are too few results
      const totalResults = Math.floor(Math.random() * 3) + 1;
      while (results.length < totalResults) {
        const randomId = `random-${crypto.randomBytes(4).toString('hex')}`;
        const similarity = Math.random() * 0.7; // Random similarity up to 0.7
        
        results.push({
          contentId: randomId,
          similarity,
          metadata: {
            contentId: randomId,
            title: `Random Content ${randomId}`,
            artist: `Random Artist ${Math.floor(Math.random() * 100)}`,
            creationYear: 2000 + Math.floor(Math.random() * 23)
          }
        });
      }
      
      // Sort by similarity (descending)
      results.sort((a, b) => b.similarity - a.similarity);
      
      return results;
    } catch (error) {
      logger.error('Failed to generate mock similarity results', { error: error.message, contentId });
      throw new Error(`Failed to generate mock similarity results: ${error.message}`);
    }
  }
}

module.exports = new AIAnalyzerService(); 