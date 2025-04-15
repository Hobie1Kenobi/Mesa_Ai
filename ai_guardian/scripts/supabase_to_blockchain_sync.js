const SupabaseConnector = require('./supabase_connector');
const SchemaMapper = require('./schema_mapper');
const EASAttestationService = require('./eas_attestation_service');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

// Configuration
const BATCH_SIZE = process.env.BATCH_SIZE || 10;
const SYNC_INTERVAL_MS = process.env.SYNC_INTERVAL_MS || 1000 * 60 * 15; // 15 minutes
const STATE_FILE = './sync_state.json';
const IS_TEST_MODE = process.argv.includes('--test');
const IS_SETUP_MODE = process.argv.includes('--setup');

// Initialize state
let syncState = { 
  lastSyncTimestamp: new Date(0).toISOString(), 
  processed: 0, 
  failed: 0,
  pendingCount: 0,
  lastRunTime: null
};

// Load existing state if available
function loadState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      const stateData = fs.readFileSync(STATE_FILE, 'utf8');
      syncState = { ...syncState, ...JSON.parse(stateData) };
      console.log(`Loaded previous sync state: Last sync at ${syncState.lastSyncTimestamp}`);
      console.log(`Previously processed: ${syncState.processed}, Failed: ${syncState.failed}`);
    } else {
      console.log('No previous sync state found, starting fresh');
    }
  } catch (error) {
    console.error('Error loading sync state:', error);
    console.log('Using default sync state');
  }
}

// Save current state
function saveState() {
  try {
    syncState.lastRunTime = new Date().toISOString();
    fs.writeFileSync(STATE_FILE, JSON.stringify(syncState, null, 2));
    console.log('Sync state saved');
  } catch (error) {
    console.error('Error saving sync state:', error);
  }
}

// Main process function - processes a batch of records
async function processBatch() {
  console.log(`\n===== Starting sync process at ${new Date().toISOString()} =====`);
  
  try {
    // Get required services
    const supabase = new SupabaseConnector();
    
    // Load schema UID from config file
    let schemaUID;
    try {
      const configPath = path.join(__dirname, 'schema_config.json');
      if (fs.existsSync(configPath)) {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        schemaUID = config.schemaUID;
        console.log(`Using schema UID from config: ${schemaUID}`);
      } else {
        schemaUID = process.env.ENHANCED_SCHEMA_UID;
        console.log(`Using schema UID from environment: ${schemaUID}`);
      }
    } catch (error) {
      console.error('Error loading schema config:', error);
      schemaUID = process.env.ENHANCED_SCHEMA_UID;
    }
    
    if (!schemaUID) {
      throw new Error('Schema UID not found. Please register a schema first with register_enhanced_schema.js');
    }
    
    const schemaMapper = new SchemaMapper(schemaUID);
    const attestationService = new EASAttestationService();
    
    // Set up the database if in setup mode
    if (IS_SETUP_MODE) {
      console.log('Setting up database...');
      await supabase.setupDatabase();
      await supabase.createSampleData();
      console.log('Database setup complete.');
      
      if (IS_TEST_MODE) {
        console.log('Test mode active - exiting after setup');
        return;
      }
    }
    
    // Fetch pending records from Supabase
    const pendingRecords = await supabase.fetchPendingAttestations(BATCH_SIZE);
    syncState.pendingCount = pendingRecords.length;
    
    console.log(`Found ${pendingRecords.length} pending records to process`);
    
    if (pendingRecords.length === 0) {
      console.log('No new records to process');
      saveState();
      return;
    }
    
    // Process each record
    for (const record of pendingRecords) {
      try {
        console.log(`\nProcessing record ${record.id}: "${record.track_title}" by "${record.artist_name}"`);
        
        // Map Supabase record to EAS schema
        const mappedData = schemaMapper.mapSupabaseRecordToSchema(record);
        
        // Validate mapped data
        schemaMapper.validateMappedData(mappedData);
        
        // Create attestation
        console.log('Creating attestation...');
        const attestationResult = await attestationService.createAttestation(mappedData);
        console.log(`Attestation created with UID: ${attestationResult.attestationUID}`);
        console.log(`Transaction Hash: ${attestationResult.transactionHash}`);
        
        // Verify the attestation
        console.log('Verifying attestation...');
        const verificationResult = await attestationService.verifyAttestation(attestationResult.attestationUID);
        
        if (verificationResult.isValid) {
          console.log('Attestation verified successfully');
        } else {
          console.warn('Attestation verification failed, but continuing');
        }
        
        // Update record status in Supabase
        await supabase.updateAttestationStatus(
          record.id,
          attestationResult.attestationUID,
          'ATTESTED'
        );
        
        syncState.processed++;
        console.log(`Successfully processed record ${record.id}`);
        
        // Add URL to view attestation
        console.log(`View attestation at: https://base-sepolia.easscan.org/attestation/view/${attestationResult.attestationUID}`);
        
        // If in test mode, only process one record
        if (IS_TEST_MODE) {
          console.log('Test mode active - processing only one record');
          break;
        }
        
      } catch (error) {
        console.error(`Error processing record ${record.id}:`, error);
        
        // Update record with error status
        try {
          await supabase.updateAttestationStatus(
            record.id,
            null,
            `ERROR: ${error.message.substring(0, 100)}`
          );
        } catch (updateError) {
          console.error('Failed to update error status:', updateError);
        }
        
        syncState.failed++;
      }
    }
    
    // Update sync state
    syncState.lastSyncTimestamp = new Date().toISOString();
    saveState();
    
    console.log(`\nSync completed at ${new Date().toISOString()}`);
    console.log(`Summary: Processed: ${syncState.processed}, Failed: ${syncState.failed}, Pending: ${syncState.pendingCount - (IS_TEST_MODE ? 1 : pendingRecords.length)}`);
    
  } catch (error) {
    console.error('Sync process failed:', error);
    saveState();
  }
}

// Main function
async function main() {
  // Load the previous state
  loadState();
  
  // Process once immediately
  await processBatch();
  
  // If not in test mode, set up interval
  if (!IS_TEST_MODE && !IS_SETUP_MODE) {
    console.log(`Setting up interval to run every ${SYNC_INTERVAL_MS / 1000 / 60} minutes`);
    setInterval(processBatch, SYNC_INTERVAL_MS);
  } else {
    console.log('Test mode or setup mode active - not setting up recurring sync');
  }
}

// Start the process
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
}); 