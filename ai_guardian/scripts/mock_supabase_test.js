const SchemaMapper = require('./schema_mapper');
const EASAttestationService = require('./eas_attestation_service');
require('dotenv').config();

// Mock Supabase data
const mockRecords = [
  {
    id: 1,
    track_title: 'Blockchain Symphony',
    artist_name: 'Crypto Collective',
    publisher: 'MESA Publishing',
    rights_type: 'both',
    jurisdiction: 'United States',
    rightsholder_name: 'Jane Smith',
    rightsholder_email: 'jane.smith@example.com',
    rightsholder_role: 'Composer',
    rightsholder_ipi: '00378495712',
    split_percentage: '60',
    rightsholder_address: '123 Blockchain Ave, San Francisco, CA',
    rightsholder_phone: '+1-555-123-4567',
    rightsholder_id: 'US-PASSPORT-483921',
    iswc_code: 'T-123456789-1',
    isrc_code: 'USRC17294831',
    designated_administrator: 'MESA Rights Management',
    wallet_address: process.env.WALLET_ADDRESS
  }
];

// Mock SupabaseConnector
class MockSupabaseConnector {
  constructor() {
    console.log('Initialized mock Supabase connector');
    this.records = [...mockRecords];
    this.updatedRecords = [];
  }
  
  async fetchPendingAttestations(limit = 10) {
    console.log(`Fetching up to ${limit} pending attestations (mock)`);
    return this.records.slice(0, limit);
  }
  
  async updateAttestationStatus(recordId, attestationUid, status) {
    console.log(`Updating record ${recordId} with status: ${status} (mock)`);
    
    const record = this.records.find(r => r.id === recordId);
    if (record) {
      record.attestation_uid = attestationUid;
      record.blockchain_status = status;
      record.last_synced = new Date().toISOString();
      this.updatedRecords.push({...record});
      console.log(`Record ${recordId} updated successfully (mock)`);
    } else {
      console.error(`Record ${recordId} not found (mock)`);
    }
    
    return record;
  }
  
  getUpdatedRecords() {
    return this.updatedRecords;
  }
}

async function runTest() {
  try {
    console.log('Starting mock Supabase integration test');
    
    // Load schema UID
    const fs = require('fs');
    let schemaUID;
    
    try {
      const configPath = './schema_config.json';
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
    
    // Initialize services
    const supabase = new MockSupabaseConnector();
    const schemaMapper = new SchemaMapper(schemaUID);
    const attestationService = new EASAttestationService();
    
    // Get records
    const pendingRecords = await supabase.fetchPendingAttestations(1);
    console.log(`Found ${pendingRecords.length} pending mock records to process`);
    
    // Process records
    for (const record of pendingRecords) {
      try {
        console.log(`\nProcessing record ${record.id}: "${record.track_title}" by "${record.artist_name}"`);
        
        // Map record to schema
        const mappedData = schemaMapper.mapSupabaseRecordToSchema(record);
        
        // Validate mapped data
        schemaMapper.validateMappedData(mappedData);
        
        // Create attestation
        console.log('Creating attestation...');
        const attestationResult = await attestationService.createAttestation(mappedData);
        console.log(`Attestation created with UID: ${attestationResult.attestationUID}`);
        
        // Update record status
        await supabase.updateAttestationStatus(
          record.id,
          attestationResult.attestationUID,
          'ATTESTED'
        );
        
        console.log(`Successfully processed record ${record.id}`);
        console.log(`View attestation at: https://base-sepolia.easscan.org/attestation/view/${attestationResult.attestationUID}`);
        
      } catch (error) {
        console.error(`Error processing record ${record.id}:`, error);
      }
    }
    
    // Check results
    const updatedRecords = supabase.getUpdatedRecords();
    console.log('\nUpdated Records:');
    console.log(JSON.stringify(updatedRecords, null, 2));
    
    console.log('\nTest complete!');
    
  } catch (error) {
    console.error('Test failed:', error);
  }
}

runTest(); 