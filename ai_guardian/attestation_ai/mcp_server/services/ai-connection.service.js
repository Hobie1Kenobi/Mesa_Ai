/**
 * AI Connection Service
 * 
 * Handles interactions with the AI agent for rights verification and analysis
 */

const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

// In-memory queue for demonstration purposes
// In a production system, this would be a proper message queue
const analysisQueue = [];
const analysisResults = new Map();

// Default AI service endpoint
let aiServiceEndpoint = process.env.AI_SERVICE_ENDPOINT || 'http://localhost:5000';

/**
 * Initialize the AI Connection service
 */
const initialize = (endpoint) => {
  if (endpoint) {
    aiServiceEndpoint = endpoint;
  }
  
  console.log(`AI Connection Service: Initialized with endpoint ${aiServiceEndpoint}`);
  
  // Start processing queue in background
  setInterval(processQueue, 5000);
};

/**
 * Submit a rights verification request to the AI service
 */
const submitRightsVerification = async (rightsData) => {
  const analysisId = uuidv4();
  
  // Add to queue
  analysisQueue.push({
    id: analysisId,
    type: 'rights-verification',
    status: 'queued',
    data: rightsData,
    submittedAt: new Date().toISOString()
  });
  
  console.log(`Submitted rights verification request with ID: ${analysisId}`);
  return { analysisId };
};

/**
 * Process the analysis queue
 * This simulates communication with an AI service
 */
const processQueue = async () => {
  if (analysisQueue.length === 0) return;
  
  const item = analysisQueue.shift();
  console.log(`Processing analysis request: ${item.id}`);
  
  try {
    // In a real implementation, this would call the AI service
    // For demo purposes, we're simulating the AI analysis
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Simulate AI analysis
    const result = simulateAIAnalysis(item);
    
    // Store the result
    analysisResults.set(item.id, {
      ...result,
      status: 'completed',
      completedAt: new Date().toISOString()
    });
    
    console.log(`Analysis completed for request: ${item.id}`);
  } catch (error) {
    console.error(`Error processing analysis request ${item.id}:`, error);
    
    // Store error result
    analysisResults.set(item.id, {
      id: item.id,
      type: item.type,
      status: 'failed',
      error: error.message,
      completedAt: new Date().toISOString()
    });
  }
};

/**
 * Simulate AI analysis results
 */
const simulateAIAnalysis = (item) => {
  const { data, type, id } = item;
  
  // For rights verification
  if (type === 'rights-verification') {
    // Random confidence score between 0.5 and 0.99
    const confidenceScore = (0.5 + Math.random() * 0.49).toFixed(2);
    
    // Verification result based on confidence
    const verificationStatus = confidenceScore > 0.8 ? 'verified' : 'requires-review';
    
    return {
      id,
      type,
      result: {
        trackId: data.trackId || id,
        trackTitle: data.trackTitle,
        artist: data.artist,
        confidenceScore,
        verificationStatus,
        analysisDetails: {
          metadataMatch: Math.random() > 0.2,
          contentMatch: Math.random() > 0.2,
          ownershipEvidence: Math.random() > 0.3 ? 'strong' : 'weak',
          recommendedAction: confidenceScore > 0.8 ? 'approve' : 'manual-review'
        }
      }
    };
  }
  
  // For other analysis types
  return {
    id,
    type,
    result: {
      status: 'unknown-analysis-type',
      message: `Unsupported analysis type: ${type}`
    }
  };
};

/**
 * Get analysis result by ID
 */
const getAnalysisResult = (analysisId) => {
  if (!analysisResults.has(analysisId)) {
    return {
      analysisId,
      status: 'not-found',
      message: 'Analysis ID not found'
    };
  }
  
  return analysisResults.get(analysisId);
};

/**
 * Connect to real AI service
 * This would be used in production to actually call an external AI service
 */
const callAIService = async (endpoint, data) => {
  try {
    const response = await axios.post(`${aiServiceEndpoint}${endpoint}`, data);
    return response.data;
  } catch (error) {
    console.error(`Error calling AI service at ${endpoint}:`, error);
    throw error;
  }
};

module.exports = {
  initialize,
  submitRightsVerification,
  getAnalysisResult
}; 