/**
 * MESA AI Guardian - MCP Server
 * 
 * Message Control Protocol server for interfacing between AI analysis
 * and the Ethereum Attestation Service (EAS)
 */

const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const { ethers } = require('ethers');
const { EAS, SchemaRegistry } = require('@ethereum-attestation-service/eas-sdk');
require('dotenv').config();

// Import routes
const schemaRoutes = require('./routes/schema.routes');
const attestationRoutes = require('./routes/attestation.routes');
const verificationRoutes = require('./routes/verification.routes');

// Import services
const easService = require('./services/eas.service');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(morgan('dev'));

// Initialize EAS connection
const initEAS = async () => {
  try {
    // Set up provider
    const provider = new ethers.providers.JsonRpcProvider(
      process.env.RPC_URL || 'https://sepolia.base.org'
    );
    
    // Set up signer if private key is provided
    let signer;
    if (process.env.PRIVATE_KEY) {
      signer = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
      console.log(`MCP: Connected with wallet address: ${signer.address}`);
    } else {
      console.log('MCP: Running in read-only mode (no private key provided)');
    }
    
    // EAS addresses (Base Sepolia)
    const EAS_CONTRACT_ADDRESS = process.env.EAS_CONTRACT_ADDRESS || '0xC2679fBD37d54388Ce493F1DB75320D236e1815e';
    const SCHEMA_REGISTRY_ADDRESS = process.env.SCHEMA_REGISTRY_ADDRESS || '0x0a7E2Ff54e76B8E6659aedc9103FB21c038050D0';
    
    // Initialize EAS SDK
    const eas = new EAS(EAS_CONTRACT_ADDRESS);
    eas.connect(signer || provider);
    
    // Initialize SchemaRegistry
    const schemaRegistry = new SchemaRegistry(SCHEMA_REGISTRY_ADDRESS);
    schemaRegistry.connect(signer || provider);
    
    // Initialize services
    await easService.initialize(eas, schemaRegistry, signer || provider);
    
    console.log('MCP: EAS connection initialized successfully');
    return { eas, schemaRegistry, provider, signer };
  } catch (error) {
    console.error('Error initializing EAS connection:', error);
    throw error;
  }
};

// Routes
app.use('/api/schema', schemaRoutes);
app.use('/api/attestation', attestationRoutes);
app.use('/api/verification', verificationRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'healthy',
    service: 'MESA AI Guardian MCP Server',
    version: '1.0.0'
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(err.status || 500).json({
    error: {
      message: err.message || 'Something went wrong',
      details: process.env.NODE_ENV === 'development' ? err.stack : undefined
    }
  });
});

// Start server
const startServer = async () => {
  try {
    await initEAS();
    
    app.listen(PORT, () => {
      console.log(`MCP: Server running on port ${PORT}`);
      console.log(`MCP: Connect AI agent to http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
};

// Start the server if this file is run directly
if (require.main === module) {
  startServer();
}

module.exports = { app, startServer }; 