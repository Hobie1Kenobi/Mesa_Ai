/**
 * Verification Routes
 * 
 * API endpoints for handling music rights verification
 * requests and attestations.
 */

const express = require('express');
const router = express.Router();
const aiConnector = require('../services/ai-connector.service');
const easService = require('../services/eas.service');

// Initialize services on startup
Promise.all([
  aiConnector.initialize('https://ai-analyzer.example.com/api', process.env.AI_API_KEY || 'demo_key'),
  easService.initialize()
])
  .then(() => console.log('All services initialized successfully for verification routes'))
  .catch(err => console.error('Failed to initialize services for verification routes:', err));

/**
 * @route   POST /api/verification/submit
 * @desc    Submit a new rights verification request
 * @access  Private (requires authentication)
 */
router.post('/submit', async (req, res) => {
  try {
    const { 
      trackId, 
      trackTitle, 
      artist, 
      rightsholder, 
      verificationTypes, 
      sourceUrl, 
      sourceFiles,
      metadata
    } = req.body;

    // Validate required fields
    if (!trackId || !trackTitle) {
      return res.status(400).json({ 
        success: false, 
        message: 'Missing required fields: trackId and trackTitle are mandatory' 
      });
    }

    // Submit verification to AI connector
    const verificationRequest = await aiConnector.submitVerification({
      trackId,
      trackTitle,
      artist,
      rightsholder,
      verificationTypes,
      sourceUrl,
      sourceFiles,
      metadata
    });

    res.status(201).json({
      success: true,
      message: 'Verification request submitted successfully',
      verification: verificationRequest
    });
  } catch (error) {
    console.error('Error submitting verification request:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to submit verification request',
      error: error.message
    });
  }
});

/**
 * @route   GET /api/verification/status/:requestId
 * @desc    Get status of a verification request
 * @access  Private (requires authentication)
 */
router.get('/status/:requestId', async (req, res) => {
  try {
    const { requestId } = req.params;

    // Get verification status from AI connector
    const verificationStatus = await aiConnector.getVerificationStatus(requestId);

    if (!verificationStatus.found) {
      return res.status(404).json({
        success: false,
        message: 'Verification request not found',
        requestId
      });
    }

    res.status(200).json({
      success: true,
      verification: verificationStatus
    });
  } catch (error) {
    console.error('Error getting verification status:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get verification status',
      error: error.message
    });
  }
});

/**
 * @route   POST /api/verification/createAttestation/:requestId
 * @desc    Create an attestation for a verified track
 * @access  Private (requires authentication)
 */
router.post('/createAttestation/:requestId', async (req, res) => {
  try {
    const { requestId } = req.params;
    const { walletAddress } = req.body;

    if (!walletAddress) {
      return res.status(400).json({
        success: false,
        message: 'Wallet address is required to create an attestation'
      });
    }

    // First check if the verification was successful
    const verificationStatus = await aiConnector.getVerificationStatus(requestId);

    if (!verificationStatus.found) {
      return res.status(404).json({
        success: false,
        message: 'Verification request not found',
        requestId
      });
    }

    if (verificationStatus.status !== 'completed') {
      return res.status(400).json({
        success: false,
        message: 'Verification is not yet completed',
        status: verificationStatus.status
      });
    }

    if (!verificationStatus.results?.results?.isVerified) {
      return res.status(400).json({
        success: false,
        message: 'Track verification failed. Cannot create attestation.',
        verificationResults: verificationStatus.results
      });
    }

    // Prepare attestation data
    const attestationData = {
      trackId: verificationStatus.trackId,
      trackTitle: verificationStatus.trackTitle,
      artist: verificationStatus.artist,
      rightsholder: walletAddress,
      verificationRequestId: requestId,
      confidenceScore: verificationStatus.results.results.confidenceScore,
      createdAt: new Date().toISOString()
    };

    // Create attestation using EAS service
    const attestation = await easService.createAttestation(attestationData, walletAddress);

    res.status(201).json({
      success: true,
      message: 'Attestation created successfully',
      attestation
    });
  } catch (error) {
    console.error('Error creating attestation:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to create attestation',
      error: error.message
    });
  }
});

/**
 * @route   GET /api/verification/attestation/:attestationUid
 * @desc    Get an attestation by its UID
 * @access  Public
 */
router.get('/attestation/:attestationUid', async (req, res) => {
  try {
    const { attestationUid } = req.params;

    // Get attestation from EAS service
    const attestation = await easService.getAttestation(attestationUid);

    if (!attestation) {
      return res.status(404).json({
        success: false,
        message: 'Attestation not found',
        attestationUid
      });
    }

    res.status(200).json({
      success: true,
      attestation
    });
  } catch (error) {
    console.error('Error getting attestation:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get attestation',
      error: error.message
    });
  }
});

/**
 * @route   POST /api/verification/verify/:attestationUid
 * @desc    Verify an attestation
 * @access  Public
 */
router.post('/verify/:attestationUid', async (req, res) => {
  try {
    const { attestationUid } = req.params;

    // Verify attestation using EAS service
    const verificationResult = await easService.verifyAttestation(attestationUid);

    res.status(200).json({
      success: true,
      message: 'Attestation verification completed',
      verification: verificationResult
    });
  } catch (error) {
    console.error('Error verifying attestation:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to verify attestation',
      error: error.message
    });
  }
});

/**
 * @route   POST /api/verification/revoke/:attestationUid
 * @desc    Revoke an attestation
 * @access  Private (requires authentication)
 */
router.post('/revoke/:attestationUid', async (req, res) => {
  try {
    const { attestationUid } = req.params;
    const { walletAddress, reason } = req.body;

    if (!walletAddress) {
      return res.status(400).json({
        success: false,
        message: 'Wallet address is required to revoke an attestation'
      });
    }

    // Revoke attestation using EAS service
    const revocationResult = await easService.revokeAttestation(attestationUid, walletAddress, reason);

    res.status(200).json({
      success: true,
      message: 'Attestation revoked successfully',
      revocation: revocationResult
    });
  } catch (error) {
    console.error('Error revoking attestation:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to revoke attestation',
      error: error.message
    });
  }
});

module.exports = router; 