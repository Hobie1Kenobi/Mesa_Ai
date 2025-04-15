const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

class SupabaseConnector {
  constructor() {
    if (!process.env.SUPABASE_URL || !process.env.SUPABASE_SERVICE_KEY) {
      throw new Error('SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file');
    }
    
    this.supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_SERVICE_KEY
    );
    
    console.log('Supabase client initialized');
  }

  async fetchNewMusicRights(lastSyncTimestamp) {
    console.log(`Fetching records updated after ${lastSyncTimestamp}`);
    
    const { data, error } = await this.supabase
      .from('music_rights')
      .select('*')
      .gt('updated_at', lastSyncTimestamp);
      
    if (error) {
      console.error('Error fetching new music rights:', error);
      throw new Error(`Supabase query error: ${error.message}`);
    }
    
    console.log(`Found ${data.length} updated records`);
    return data;
  }
  
  async updateAttestationStatus(recordId, attestationUid, status) {
    console.log(`Updating record ${recordId} with status: ${status}`);
    
    const { data, error } = await this.supabase
      .from('music_rights')
      .update({ 
        attestation_uid: attestationUid,
        blockchain_status: status,
        last_synced: new Date().toISOString()
      })
      .eq('id', recordId);
      
    if (error) {
      console.error('Error updating attestation status:', error);
      throw new Error(`Failed to update record status: ${error.message}`);
    }
    
    console.log(`Record ${recordId} updated successfully`);
    return data;
  }
  
  async fetchPendingAttestations(limit = 50) {
    console.log(`Fetching up to ${limit} pending attestations...`);
    
    const { data, error } = await this.supabase
      .from('music_rights')
      .select('*')
      .is('attestation_uid', null)
      .limit(limit);
      
    if (error) {
      console.error('Error fetching pending attestations:', error);
      throw new Error(`Supabase query error: ${error.message}`);
    }
    
    console.log(`Found ${data.length} pending attestations`);
    return data;
  }
  
  async createSampleData() {
    console.log('Creating sample test data in Supabase...');
    
    const sampleData = [
      {
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
        wallet_address: process.env.WALLET_ADDRESS || '0xbDE22Ea0D5d21925f8c64d28c0b1a376763a76d8'
      },
      {
        track_title: 'Decentralized Melody',
        artist_name: 'Web3 Ensemble',
        publisher: 'Base Records',
        rights_type: 'songwriting',
        jurisdiction: 'European Union',
        rightsholder_name: 'Marcus Johnson',
        rightsholder_email: 'marcus@web3music.io',
        rightsholder_role: 'Lyricist',
        rightsholder_ipi: '00492837561',
        split_percentage: '75',
        rightsholder_address: '45 Digital Street, Berlin, Germany',
        rightsholder_phone: '+49-555-789-1234',
        rightsholder_id: 'DE-ID-78392183',
        iswc_code: 'T-987654321-2',
        isrc_code: null,
        designated_administrator: 'MESA Rights Management',
        wallet_address: process.env.WALLET_ADDRESS || '0xbDE22Ea0D5d21925f8c64d28c0b1a376763a76d8'
      }
    ];
    
    for (const sample of sampleData) {
      const { data, error } = await this.supabase
        .from('music_rights')
        .insert(sample);
        
      if (error) {
        console.error('Error inserting sample data:', error);
        throw new Error(`Failed to insert sample data: ${error.message}`);
      }
    }
    
    console.log('Sample data created successfully');
  }
  
  async setupDatabase() {
    console.log('Setting up music_rights table in Supabase...');
    
    // This assumes you have enough permissions in Supabase to create tables
    // In many cases, you would create the table through the Supabase dashboard instead
    const { error } = await this.supabase.rpc('create_music_rights_table');
    
    if (error) {
      console.error('Error creating table:', error);
      console.log('You may need to create the table manually in the Supabase dashboard');
      return false;
    }
    
    console.log('Table created successfully');
    return true;
  }
}

// Allow direct execution for testing
if (require.main === module) {
  const test = async () => {
    try {
      const connector = new SupabaseConnector();
      
      // Test connection
      console.log('Testing Supabase connection...');
      const { data, error } = await connector.supabase.from('music_rights').select('count()', { count: 'exact' });
      
      if (error) {
        console.error('Connection test failed:', error);
        console.log('You might need to create the table first');
      } else {
        console.log(`Connection successful. Table has ${data[0].count} records.`);
      }
      
    } catch (error) {
      console.error('Test failed:', error);
    }
  };
  
  test();
}

module.exports = SupabaseConnector; 