const axios = require('axios');
const fs = require('fs').promises;

// Base Sepolia EAS URLs and configuration
const BASE_SEPOLIA_RPC = 'https://sepolia.base.org';
const EAS_CONTRACT = '0xC2679fBD37d54388Ce493F1DB75320D236e1815e';
const MCP_SERVER = 'http://localhost:3001';

async function queryAttestation(attestationUID) {
  try {
    console.log(`Querying attestation UID: ${attestationUID}`);
    
    // Query the MCP Server
    const response = await axios.get(`${MCP_SERVER}/api/attestation/${attestationUID}`);
    
    console.log("\n=== Attestation Data ===");
    console.log(JSON.stringify(response.data, null, 2));
    
    return response.data;
  } catch (error) {
    console.error('Error querying attestation:', error.message);
    if (error.response) {
      console.error('Response data:', error.response.data);
    }
  }
}

async function submitVerification(musicData) {
  try {
    console.log(`Submitting rights for verification: ${musicData.trackTitle} by ${musicData.artist}`);
    
    // Submit to the MCP server for verification
    const response = await axios.post(`${MCP_SERVER}/api/rights/verify`, musicData);
    
    console.log("\n=== Verification Request Submitted ===");
    console.log(JSON.stringify(response.data, null, 2));
    
    return response.data;
  } catch (error) {
    console.error('Error submitting verification request:', error.message);
    if (error.response) {
      console.error('Response data:', error.response.data);
    }
  }
}

async function checkVerificationStatus(analysisId) {
  try {
    console.log(`Checking verification status for analysis ID: ${analysisId}`);
    
    // Check status at the MCP server
    const response = await axios.get(`${MCP_SERVER}/api/rights/verify/${analysisId}`);
    
    console.log("\n=== Verification Status ===");
    console.log(JSON.stringify(response.data, null, 2));
    
    return response.data;
  } catch (error) {
    console.error('Error checking verification status:', error.message);
    if (error.response) {
      console.error('Response data:', error.response.data);
    }
  }
}

async function createAttestation(analysisId, rightsData) {
  try {
    console.log(`Creating attestation for verified rights (Analysis ID: ${analysisId})`);
    
    // Create attestation at the MCP server
    const response = await axios.post(`${MCP_SERVER}/api/rights/attest`, {
      analysisId,
      rightsData
    });
    
    console.log("\n=== Attestation Created ===");
    console.log(JSON.stringify(response.data, null, 2));
    
    return response.data;
  } catch (error) {
    console.error('Error creating attestation:', error.message);
    if (error.response) {
      console.error('Response data:', error.response.data);
    }
  }
}

async function processCSVFile(csvPath) {
  try {
    console.log(`Processing CSV file: ${csvPath}`);
    
    // Read and parse CSV
    const csvData = await fs.readFile(csvPath, 'utf8');
    const rows = csvData.split('\n').map(row => row.split(','));
    
    // Extract headers
    const headers = rows[0];
    
    // Process each row (skip header row)
    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      if (row.length <= 1) continue; // Skip empty rows
      
      // Create a data object from the row
      const musicData = {};
      for (let j = 0; j < headers.length && j < row.length; j++) {
        musicData[headers[j].trim()] = row[j].trim();
      }
      
      // Submit for verification
      console.log(`\nProcessing track: ${musicData.trackTitle || musicData.title || 'Unknown'}`);
      const verificationResult = await submitVerification({
        trackId: musicData.trackId || `track-${i}`,
        trackTitle: musicData.trackTitle || musicData.title || 'Unknown Title',
        artist: musicData.artist || 'Unknown Artist',
        rightsholder: musicData.rightsholder || musicData.publisher || 'Unknown Publisher'
      });
      
      if (verificationResult && verificationResult.analysisId) {
        // Check status after a few seconds
        console.log('Waiting for verification to complete...');
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        const statusResult = await checkVerificationStatus(verificationResult.analysisId);
        
        // If verification successful, create attestation
        if (statusResult && statusResult.status === 'completed' && 
            statusResult.result && statusResult.result.verificationStatus === 'verified') {
          
          await createAttestation(verificationResult.analysisId, musicData);
        }
      }
      
      // Add a small delay between processing items
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    console.log('\nCSV processing completed!');
  } catch (error) {
    console.error('Error processing CSV file:', error.message);
  }
}

// Main function to handle command line arguments
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  
  if (!command) {
    console.log(`
MESA AI Guardian CLI
Usage:
  node eas-query.js <command> [arguments]

Commands:
  query <attestationUID>          Query an attestation by UID
  verify <trackTitle> <artist>    Submit rights for verification
  status <analysisId>             Check verification status
  attest <analysisId>             Create attestation for verified rights
  process-csv <csvFilePath>       Process a CSV file of tracks
`);
    return;
  }
  
  switch (command) {
    case 'query':
      if (!args[1]) {
        console.error('Please provide an attestation UID');
        return;
      }
      await queryAttestation(args[1]);
      break;
      
    case 'verify':
      if (!args[1] || !args[2]) {
        console.error('Please provide track title and artist');
        return;
      }
      await submitVerification({
        trackId: `track-${Date.now()}`,
        trackTitle: args[1],
        artist: args[2],
        rightsholder: args[3] || 'Unknown Publisher'
      });
      break;
      
    case 'status':
      if (!args[1]) {
        console.error('Please provide an analysis ID');
        return;
      }
      await checkVerificationStatus(args[1]);
      break;
      
    case 'attest':
      if (!args[1]) {
        console.error('Please provide an analysis ID');
        return;
      }
      await createAttestation(args[1], {
        trackId: `track-${Date.now()}`,
        trackTitle: args[2] || 'Unknown Title',
        artist: args[3] || 'Unknown Artist',
        rightsholder: args[4] || 'Unknown Publisher'
      });
      break;
      
    case 'process-csv':
      if (!args[1]) {
        console.error('Please provide a CSV file path');
        return;
      }
      await processCSVFile(args[1]);
      break;
      
    default:
      console.error(`Unknown command: ${command}`);
      break;
  }
}

main(); 