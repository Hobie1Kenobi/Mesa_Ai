require('dotenv').config();

class SchemaMapper {
  constructor(schemaId) {
    this.schemaId = schemaId;
    console.log(`Schema mapper initialized with schema: ${schemaId}`);
  }
  
  mapSupabaseRecordToSchema(record) {
    console.log(`Mapping record ${record.id}: ${record.track_title}`);
    
    // Transform Supabase record into EAS schema format with all requested fields
    return {
      // Core identifiers
      track_title: record.track_title,
      artist_name: record.artist_name,
      publisher: record.publisher || "MESA Music Publishing",
      
      // Rights classification
      rights_type: record.rights_type || "both", // songwriting, master, or both
      jurisdiction: record.jurisdiction || "International",
      
      // Rights owner details
      rightsholder_name: record.rightsholder_name,
      rightsholder_email: record.rightsholder_email || "",
      rightsholder_role: record.rightsholder_role || "",
      rightsholder_ipi: record.rightsholder_ipi || "",
      split_percentage: record.split_percentage || "100",
      rightsholder_address: record.rightsholder_address || "",
      rightsholder_phone: record.rightsholder_phone || "",
      rightsholder_id: record.rightsholder_id || "",
      
      // Additional metadata
      iswc_code: record.iswc_code || this._generatePlaceholderId("T"),
      isrc_code: record.isrc_code || "",
      designated_administrator: record.designated_administrator || "",
      
      // Blockchain data
      wallet_address: record.wallet_address || process.env.WALLET_ADDRESS,
      
      // Validation data
      mesa_verified: "true"
    };
  }
  
  _generatePlaceholderId(prefix) {
    const randomPart = Math.floor(Math.random() * 1000000000).toString().padStart(9, '0');
    const checkDigit = Math.floor(Math.random() * 10);
    return `${prefix}-${randomPart}-${checkDigit}`;
  }
  
  validateMappedData(mappedData) {
    console.log('Validating mapped data...');
    
    // Ensure all required fields are present
    const requiredFields = [
      'track_title', 
      'artist_name', 
      'rights_type', 
      'rightsholder_name', 
      'split_percentage', 
      'wallet_address'
    ];
    
    const missingFields = requiredFields.filter(field => !mappedData[field]);
    
    if (missingFields.length > 0) {
      const errorMsg = `Missing required fields: ${missingFields.join(', ')}`;
      console.error(errorMsg);
      throw new Error(errorMsg);
    }
    
    console.log('Validation passed');
    return true;
  }
  
  // Helper to convert an address string to a valid Ethereum address
  normalizeAddress(address) {
    if (!address) return process.env.WALLET_ADDRESS;
    
    // If it's already a valid address pattern, return it
    if (/^0x[a-fA-F0-9]{40}$/.test(address)) {
      return address;
    }
    
    // Otherwise use default wallet address
    return process.env.WALLET_ADDRESS;
  }
}

// Allow direct execution for testing
if (require.main === module) {
  const test = async () => {
    console.log('Testing schema mapper...');
    
    // Use a placeholder schema ID for testing
    const mapper = new SchemaMapper('0x0000000000000000000000000000000000000000000000000000000000000000');
    
    // Create a sample record
    const sampleRecord = {
      id: 1,
      track_title: 'Test Track',
      artist_name: 'Test Artist',
      publisher: 'Test Publisher',
      rights_type: 'both',
      rightsholder_name: 'Test Rights Holder',
      split_percentage: '100',
      wallet_address: '0x0000000000000000000000000000000000000000'
    };
    
    // Test mapping
    const mapped = mapper.mapSupabaseRecordToSchema(sampleRecord);
    console.log('Mapped data:', mapped);
    
    // Test validation
    try {
      mapper.validateMappedData(mapped);
      console.log('Validation success!');
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };
  
  test();
}

module.exports = SchemaMapper; 