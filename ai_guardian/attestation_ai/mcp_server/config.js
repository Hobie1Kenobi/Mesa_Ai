/**
 * MCP Server Configuration
 * 
 * Configuration settings for the Music Content Protection server.
 */

require('dotenv').config();

module.exports = {
  server: {
    port: process.env.PORT || 3001,
    host: process.env.HOST || 'localhost',
  },
  
  blockchain: {
    // EAS Schema constants
    easContractAddress: process.env.EAS_CONTRACT_ADDRESS || '0xC2679fBD37d54388Ce493F1DB75320D236e1815e', // Sepolia
    easSchemaUID: process.env.EAS_SCHEMA_UID || '0x0d8026ba54409df0a7ecf71c9e0a29e8f2faaf3ea12b138d0a0c1ecf69c7ca98',
    provider: process.env.ETHEREUM_RPC_URL || 'https://sepolia.infura.io/v3/YOUR_INFURA_KEY',
    
    // Default private key for testing - should be overridden in .env for production
    privateKey: process.env.PRIVATE_KEY || '0x0000000000000000000000000000000000000000000000000000000000000000', 
    
    // Gas settings
    gasLimit: process.env.GAS_LIMIT || 3000000,
    maxFeePerGas: process.env.MAX_FEE_PER_GAS || '50000000000', // 50 gwei
    maxPriorityFeePerGas: process.env.MAX_PRIORITY_FEE_PER_GAS || '2000000000', // 2 gwei
  },
  
  ai: {
    apiKey: process.env.OPENAI_API_KEY || '',
    model: process.env.AI_MODEL || 'gpt-4o',
    cacheTTL: parseInt(process.env.CACHE_TTL) || 86400000, // 24 hours
  },
  
  storage: {
    type: process.env.STORAGE_TYPE || 'local', // 'local', 's3', 'ipfs'
    localPath: process.env.STORAGE_LOCAL_PATH || './data',
    s3: {
      bucket: process.env.S3_BUCKET || 'mesa-ai-guardian',
      region: process.env.S3_REGION || 'us-east-1',
      accessKeyId: process.env.S3_ACCESS_KEY_ID,
      secretAccessKey: process.env.S3_SECRET_ACCESS_KEY,
    },
    ipfs: {
      gateway: process.env.IPFS_GATEWAY || 'https://ipfs.io/ipfs/',
      pinningService: process.env.IPFS_PINNING_SERVICE || 'pinata',
      pinataApiKey: process.env.PINATA_API_KEY,
      pinataSecretApiKey: process.env.PINATA_SECRET_API_KEY,
    },
  },
  
  auth: {
    jwtSecret: process.env.JWT_SECRET || 'your-secret-key',
    jwtExpiresIn: process.env.JWT_EXPIRES_IN || '1d',
  },
  
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    file: process.env.LOG_FILE || 'mcp-server.log',
  },
  
  // Flag for testing environments
  isTest: process.env.NODE_ENV === 'test',
  
  // Flag for using mock data and services
  mockMode: process.env.MOCK_MODE === 'true',
  
  // CORS configuration
  cors: {
    origins: (process.env.CORS_ORIGINS || '*').split(','),
    methods: (process.env.CORS_METHODS || 'GET,HEAD,PUT,PATCH,POST,DELETE').split(','),
  },
  
  // Rate limiting
  rateLimit: {
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15 minutes
    max: parseInt(process.env.RATE_LIMIT_MAX) || 100, // limit each IP to 100 requests per windowMs
  }
}; 