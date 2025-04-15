/**
 * Attestation Routes
 * 
 * These routes handle all attestation-related operations including:
 * - Creating attestations for music content
 * - Verifying attestations
 * - Retrieving attestation data
 * - Revoking attestations
 */

const express = require('express');
const router = express.Router();
const { body, param, query, validationResult } = require('express-validator');
const easService = require('../services/eas.service');
const aiAnalyzerService = require('../services/ai-analyzer.service');
const contentService = require('../services/content.service');
const authMiddleware = require('../middleware/auth.middleware');
const logger = require('../utils/logger');

/**
 * Create an attestation for music content
 * 
 * POST /api/attestations
 */
router.post('/',
  authMiddleware.authenticate,
  [
    body('contentId').notEmpty().withMessage('Content ID is required'),
    body('title').notEmpty().withMessage('Title is required'),
    body('artist').notEmpty().withMessage('Artist is required'),
    body('publisher').notEmpty().withMessage('Publisher is required'),
    body('creationYear').isInt({ min: 1900, max: new Date().getFullYear() })
      .withMessage(`Creation year must be between 1900 and ${new Date().getFullYear()}`),
    body('metadataURI').optional(),
    body('isOriginal').isBoolean().withMessage('isOriginal must be a boolean value'),
    body('recipient').optional().isEthereumAddress().withMessage('Invalid Ethereum address')
  ],
  async (req, res) => {
    try {
      // Validate input
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      // Extract music content data from request
      const musicData = {
        contentId: req.body.contentId,
        title: req.body.title,
        artist: req.body.artist,
        publisher: req.body.publisher,
        creationYear: req.body.creationYear,
        metadataURI: req.body.metadataURI || '',
        isOriginal: req.body.isOriginal
      };

      // Get recipient address (can be null for zero address)
      const recipient = req.body.recipient || null;

      // First, store the content data
      await contentService.storeContentData(musicData);

      // Create attestation
      const attestation = await easService.createAttestation(musicData, recipient);
      
      // Update content record with attestation data
      await contentService.updateContentWithAttestation(
        musicData.contentId, 
        attestation.attestationUID
      );

      logger.info('Attestation created successfully', {
        contentId: musicData.contentId,
        attestationUID: attestation.attestationUID,
        user: req.user.id
      });

      res.status(201).json(attestation);
    } catch (error) {
      logger.error('Failed to create attestation', { error: error.message, stack: error.stack });
      res.status(500).json({ 
        error: 'Failed to create attestation',
        details: error.message 
      });
    }
  }
);

/**
 * Verify music content and create attestation
 * 
 * POST /api/attestations/verify
 */
router.post('/verify',
  authMiddleware.authenticate,
  [
    body('contentId').notEmpty().withMessage('Content ID is required'),
    body('title').notEmpty().withMessage('Title is required'),
    body('artist').notEmpty().withMessage('Artist is required'),
    body('publisher').notEmpty().withMessage('Publisher is required'),
    body('creationYear').isInt({ min: 1900, max: new Date().getFullYear() })
      .withMessage(`Creation year must be between 1900 and ${new Date().getFullYear()}`),
    body('contentURI').notEmpty().withMessage('Content URI is required'),
    body('metadataURI').optional(),
    body('isOriginal').isBoolean().withMessage('isOriginal must be a boolean value'),
    body('recipient').optional().isEthereumAddress().withMessage('Invalid Ethereum address')
  ],
  async (req, res) => {
    try {
      // Validate input
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      // Extract music content data from request
      const musicData = {
        contentId: req.body.contentId,
        title: req.body.title,
        artist: req.body.artist,
        publisher: req.body.publisher,
        creationYear: req.body.creationYear,
        contentURI: req.body.contentURI,
        metadataURI: req.body.metadataURI || '',
        isOriginal: req.body.isOriginal
      };

      // Get recipient address (can be null for zero address)
      const recipient = req.body.recipient || null;

      // First, store the content data
      await contentService.storeContentData(musicData);

      // Start the verification process (will be async)
      await aiAnalyzerService.analyzeContent(
        musicData.contentId,
        musicData.contentURI,
        {
          title: musicData.title,
          artist: musicData.artist,
          publisher: musicData.publisher
        }
      );

      res.status(202).json({
        message: 'Content verification started',
        contentId: musicData.contentId,
        status: 'pending'
      });
    } catch (error) {
      logger.error('Failed to start content verification', { error: error.message, stack: error.stack });
      res.status(500).json({ 
        error: 'Failed to start content verification',
        details: error.message 
      });
    }
  }
);

/**
 * Get attestation by UID
 * 
 * GET /api/attestations/:uid
 */
router.get('/:uid',
  [
    param('uid').matches(/^0x[a-fA-F0-9]{64}$/).withMessage('Invalid attestation UID format')
  ],
  async (req, res) => {
    try {
      // Validate input
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const attestationUID = req.params.uid;
      
      // Verify attestation
      const attestation = await easService.verifyAttestation(attestationUID);
      
      res.status(200).json(attestation);
    } catch (error) {
      logger.error('Failed to get attestation', { 
        error: error.message, 
        attestationUID: req.params.uid 
      });
      
      if (error.message.includes('Attestation not found')) {
        return res.status(404).json({ 
          error: 'Attestation not found',
          details: error.message 
        });
      }
      
      res.status(500).json({ 
        error: 'Failed to get attestation',
        details: error.message 
      });
    }
  }
);

/**
 * Get attestations by content ID
 * 
 * GET /api/attestations/content/:contentId
 */
router.get('/content/:contentId',
  [
    param('contentId').notEmpty().withMessage('Content ID is required')
  ],
  async (req, res) => {
    try {
      // Validate input
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const contentId = req.params.contentId;
      
      // Get content data with attestation details
      const contentData = await contentService.getContentDataByContentId(contentId);
      
      if (!contentData) {
        return res.status(404).json({ error: 'Content not found' });
      }
      
      // If there's an attestation UID, verify it
      if (contentData.attestationUID) {
        try {
          const attestation = await easService.verifyAttestation(contentData.attestationUID);
          contentData.attestation = attestation;
        } catch (attestationError) {
          contentData.attestation = { 
            error: attestationError.message,
            isValid: false
          };
        }
      }
      
      res.status(200).json(contentData);
    } catch (error) {
      logger.error('Failed to get content attestation', { 
        error: error.message, 
        contentId: req.params.contentId 
      });
      res.status(500).json({ 
        error: 'Failed to get content attestation',
        details: error.message 
      });
    }
  }
);

/**
 * Get all attestations with filtering options
 * 
 * GET /api/attestations?publisher=X&artist=Y&limit=Z
 */
router.get('/',
  [
    query('publisher').optional(),
    query('artist').optional(),
    query('title').optional(),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100'),
    query('offset').optional().isInt({ min: 0 }).withMessage('Offset must be a positive integer')
  ],
  async (req, res) => {
    try {
      // Validate input
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      // Parse query parameters
      const filters = {};
      if (req.query.publisher) filters.publisher = req.query.publisher;
      if (req.query.artist) filters.artist = req.query.artist;
      if (req.query.title) filters.title = req.query.title;
      
      const limit = parseInt(req.query.limit) || 20;
      const offset = parseInt(req.query.offset) || 0;
      
      // Get content data with pagination
      const contentList = await contentService.getAllContent(filters, limit, offset);
      
      // Get attestation details for each content item
      const results = await Promise.all(contentList.map(async (content) => {
        if (content.attestationUID) {
          try {
            const attestation = await easService.verifyAttestation(content.attestationUID);
            content.attestation = attestation;
          } catch (error) {
            content.attestation = { 
              error: error.message,
              isValid: false
            };
          }
        }
        return content;
      }));
      
      res.status(200).json({
        count: results.length,
        offset,
        limit,
        results
      });
    } catch (error) {
      logger.error('Failed to get attestations', { error: error.message, stack: error.stack });
      res.status(500).json({ 
        error: 'Failed to get attestations',
        details: error.message 
      });
    }
  }
);

/**
 * Revoke an attestation
 * 
 * DELETE /api/attestations/:uid
 */
router.delete('/:uid',
  authMiddleware.authenticate,
  authMiddleware.checkRole(['admin', 'publisher']),
  [
    param('uid').matches(/^0x[a-fA-F0-9]{64}$/).withMessage('Invalid attestation UID format')
  ],
  async (req, res) => {
    try {
      // Validate input
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const attestationUID = req.params.uid;
      
      // Get the attestation to check ownership
      const attestation = await easService.verifyAttestation(attestationUID);
      
      // Check if user is authorized to revoke (admin can revoke any, publisher only their own)
      if (req.user.role !== 'admin') {
        // Check if the attestation is owned by this publisher
        const contentData = await contentService.getContentDataByAttestationUID(attestationUID);
        
        if (!contentData || contentData.publisher !== req.user.publisher) {
          return res.status(403).json({ 
            error: 'Not authorized to revoke this attestation' 
          });
        }
      }
      
      // Revoke the attestation
      const revocationResult = await easService.revokeAttestation(attestationUID);
      
      // Update content status
      await contentService.updateContentStatus(
        attestation.musicData.contentId, 
        'revoked',
        { revocationReason: req.body.reason || 'Not specified' }
      );
      
      logger.info('Attestation revoked successfully', {
        attestationUID,
        user: req.user.id,
        role: req.user.role
      });
      
      res.status(200).json(revocationResult);
    } catch (error) {
      logger.error('Failed to revoke attestation', { 
        error: error.message, 
        attestationUID: req.params.uid,
        user: req.user?.id
      });
      
      if (error.message.includes('Attestation not found')) {
        return res.status(404).json({ 
          error: 'Attestation not found',
          details: error.message 
        });
      }
      
      if (error.message.includes('already revoked')) {
        return res.status(400).json({ 
          error: 'Attestation is already revoked',
          details: error.message 
        });
      }
      
      res.status(500).json({ 
        error: 'Failed to revoke attestation',
        details: error.message 
      });
    }
  }
);

module.exports = router; 