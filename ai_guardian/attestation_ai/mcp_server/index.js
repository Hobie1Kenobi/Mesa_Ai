/**
 * MCP (Media Control Platform) Server
 * 
 * Main entry point for the MCP server that handles:
 * - API endpoints for music rights registration
 * - AI analysis integration
 * - EAS (Ethereum Attestation Service) integration
 */

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Import services
const easService = require('./services/eas.service');
const aiConnectionService = require('./services/ai-connection.service');

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Initialize services
const initializeServices = async () => {
  try {
    // Initialize EAS service with provider from environment
    await easService.initialize(
      process.env.RPC_URL || 'https://sepolia.infura.io/v3/your-infura-key',
      process.env.PRIVATE_KEY // Private key for transactions
    );
    
    // Initialize AI Connection service
    aiConnectionService.initialize(process.env.AI_SERVICE_ENDPOINT);
    
    console.log('All services initialized successfully');
  } catch (error) {
    console.error('Error initializing services:', error);
    process.exit(1);
  }
};

// API Routes

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Submit rights for AI verification
app.post('/api/rights/verify', async (req, res) => {
  try {
    const rightsData = req.body;
    
    // Validate request
    if (!rightsData.trackTitle || !rightsData.artist) {
      return res.status(400).json({ 
        error: 'Invalid request', 
        message: 'Track title and artist are required' 
      });
    }
    
    // Submit to AI service for verification
    const { analysisId } = await aiConnectionService.submitRightsVerification(rightsData);
    
    res.status(202).json({
      status: 'processing',
      analysisId,
      message: 'Rights verification submitted for processing'
    });
  } catch (error) {
    console.error('Error in rights verification:', error);
    res.status(500).json({ error: 'Server error', message: error.message });
  }
});

// Get verification result
app.get('/api/rights/verify/:analysisId', async (req, res) => {
  try {
    const { analysisId } = req.params;
    const result = aiConnectionService.getAnalysisResult(analysisId);
    
    if (result.status === 'not-found') {
      return res.status(404).json(result);
    }
    
    res.status(200).json(result);
  } catch (error) {
    console.error('Error getting verification result:', error);
    res.status(500).json({ error: 'Server error', message: error.message });
  }
});

// Create attestation for verified rights
app.post('/api/rights/attest', async (req, res) => {
  try {
    const { analysisId, rightsData } = req.body;
    
    // Validate request
    if (!analysisId || !rightsData) {
      return res.status(400).json({ 
        error: 'Invalid request', 
        message: 'Analysis ID and rights data are required' 
      });
    }
    
    // Get analysis result
    const analysisResult = aiConnectionService.getAnalysisResult(analysisId);
    
    if (analysisResult.status === 'not-found') {
      return res.status(404).json({
        error: 'Analysis not found',
        message: `No analysis found with ID: ${analysisId}`
      });
    }
    
    if (analysisResult.status !== 'completed') {
      return res.status(400).json({
        error: 'Analysis incomplete',
        message: `Analysis with ID ${analysisId} is still in progress or failed`
      });
    }
    
    // Verify that analysis result indicates rights are valid
    if (analysisResult.result.verificationStatus !== 'verified') {
      return res.status(400).json({
        error: 'Verification failed',
        message: 'Rights verification did not pass the required threshold',
        details: analysisResult.result
      });
    }
    
    // Create attestation for the rights
    const attestationData = {
      trackId: rightsData.trackId || analysisResult.result.trackId,
      trackTitle: rightsData.trackTitle,
      artist: rightsData.artist,
      rightsholder: rightsData.rightsholder,
      timestamp: new Date().toISOString(),
      aiVerified: true,
      confidenceScore: analysisResult.result.confidenceScore
    };
    
    const attestation = await easService.createAttestation(attestationData);
    
    res.status(201).json({
      status: 'success',
      message: 'Rights attestation created successfully',
      attestation
    });
  } catch (error) {
    console.error('Error in rights attestation:', error);
    res.status(500).json({ error: 'Server error', message: error.message });
  }
});

// Get attestation by UID
app.get('/api/attestation/:uid', async (req, res) => {
  try {
    const { uid } = req.params;
    const attestation = await easService.getAttestation(uid);
    
    if (!attestation) {
      return res.status(404).json({
        error: 'Attestation not found',
        message: `No attestation found with UID: ${uid}`
      });
    }
    
    res.status(200).json(attestation);
  } catch (error) {
    console.error('Error getting attestation:', error);
    res.status(500).json({ error: 'Server error', message: error.message });
  }
});

// Start server
app.listen(PORT, async () => {
  console.log(`MCP Server running on port ${PORT}`);
  await initializeServices();
}); 