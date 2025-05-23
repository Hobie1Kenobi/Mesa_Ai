const fs = require('fs');
const axios = require('axios');
const crypto = require('crypto');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const path = require('path');
const os = require('os');

// Number of parallel workers (default to CPU count)
const NUM_WORKERS = os.cpus().length;

// EAS GraphQL endpoint
const EAS_GRAPHQL_URL = 'https://base-sepolia.easscan.org/graphql';

// Schema UID for music rights
const MUSIC_SCHEMA_UID = '0x0d8026ba54409df0a7ecf71c9e0a29e8f2faaf3ea12b138d0a0c1ecf69c7ca98';

// Main thread logic
if (isMainThread) {
  async function main() {
    const csvFilePath = process.argv[2];
    if (!csvFilePath) {
      console.error('Please provide a CSV file path');
      console.error('Usage: node eas-parallel-search.js <csv-file>');
      process.exit(1);
    }

    console.log(`Starting EAS parallel search on ${csvFilePath}`);
    console.log(`Using ${NUM_WORKERS} parallel workers`);

    // Read and parse CSV
    const tracks = await parseCSV(csvFilePath);
    console.log(`Loaded ${tracks.length} tracks from CSV`);

    // Create results directory
    const outputDir = path.join(path.dirname(csvFilePath), 'analysis_results');
    fs.mkdirSync(outputDir, { recursive: true });
    
    // Create output streams
    const matchesStream = fs.createWriteStream(path.join(outputDir, 'blockchain_matches.csv'));
    matchesStream.write('TrackId,Title,Artist,Publisher,AttestationUID,Attester,TimeCreated,OnChainData\n');

    // Split tracks into chunks for workers
    const chunkSize = Math.ceil(tracks.length / NUM_WORKERS);
    const chunks = [];
    
    for (let i = 0; i < tracks.length; i += chunkSize) {
      chunks.push(tracks.slice(i, i + chunkSize));
    }
    
    console.log(`Distributing work across ${chunks.length} workers...`);
    
    // Track global progress
    let totalProcessed = 0;
    const totalTracks = tracks.length;
    const startTime = Date.now();
    
    // Create workers and distribute chunks
    let completedWorkers = 0;
    let totalMatches = 0;
    
    const workerPromises = chunks.map((chunk, index) => {
      return new Promise((resolve) => {
        const worker = new Worker(__filename, {
          workerData: { 
            trackChunk: chunk, 
            workerId: index 
          }
        });
        
        worker.on('message', (message) => {
          if (message.type === 'match') {
            // Write match to CSV
            const match = message.data;
            matchesStream.write(`${match.trackId},${match.title},${match.artist},${match.publisher},${match.attestationUID},${match.attester},${match.timeCreated},${JSON.stringify(match.onChainData)}\n`);
            totalMatches++;
            console.log(`✅ MATCH FOUND: "${match.title}" by ${match.artist}`);
          } else if (message.type === 'progress') {
            // Update progress
            totalProcessed += message.processed;
            
            // Calculate overall progress and ETA
            const percentComplete = (totalProcessed / totalTracks * 100).toFixed(2);
            const elapsedSecs = (Date.now() - startTime) / 1000;
            const tracksPerSecond = totalProcessed / elapsedSecs;
            
            let eta = 'unknown';
            if (tracksPerSecond > 0) {
              const secsRemaining = (totalTracks - totalProcessed) / tracksPerSecond;
              eta = formatTime(secsRemaining);
            }
            
            console.log(`Progress: ${totalProcessed}/${totalTracks} tracks (${percentComplete}%) | Speed: ${tracksPerSecond.toFixed(2)} tracks/sec | ETA: ${eta} | Matches: ${totalMatches}`);
          }
        });
        
        worker.on('error', (err) => {
          console.error(`Worker ${index} error:`, err);
          resolve();
        });
        
        worker.on('exit', () => {
          completedWorkers++;
          console.log(`Worker ${index} completed. (${completedWorkers}/${chunks.length} workers done)`);
          resolve();
        });
      });
    });
    
    // Wait for all workers to complete
    await Promise.all(workerPromises);
    
    // Close output stream
    matchesStream.end();
    
    // Show final stats
    const totalTimeSeconds = (Date.now() - startTime) / 1000;
    console.log('\n==================================');
    console.log('EAS Parallel Search Complete');
    console.log('==================================');
    console.log(`Total tracks processed: ${totalTracks}`);
    console.log(`Total on-chain matches found: ${totalMatches}`);
    console.log(`Time taken: ${formatTime(totalTimeSeconds)}`);
    console.log(`Average processing speed: ${(totalTracks / totalTimeSeconds).toFixed(2)} tracks/second`);
    console.log(`Results saved to: ${path.join(outputDir, 'blockchain_matches.csv')}`);
    console.log('==================================');
  }
  
  function formatTime(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    return `${hrs}h ${mins}m ${secs}s`;
  }
  
  async function parseCSV(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    const tracks = [];
    for (let i = 1; i < lines.length; i++) {
      if (lines[i].trim() === '') continue;
      
      const fields = lines[i].split(',');
      const track = {};
      
      for (let j = 0; j < headers.length && j < fields.length; j++) {
        track[headers[j]] = fields[j].trim();
      }
      
      // Map standard fields regardless of CSV format
      track.title = track.title || track.trackTitle || track['Track Title'] || '';
      track.artist = track.artist || track['Primary Artist'] || '';
      track.publisher = track.publisher || track.Publisher || track.rightsholder || '';
      track.trackId = track.trackId || track.id || `track-${i}`;
      
      // Only include tracks with at least title and artist
      if (track.title && track.artist) {
        tracks.push(track);
      }
    }
    
    return tracks;
  }
  
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
} 
// Worker thread logic
else {
  async function workerMain() {
    const { trackChunk, workerId } = workerData;
    console.log(`Worker ${workerId} started with ${trackChunk.length} tracks`);
    
    // Process tracks in batches to avoid overwhelming the EAS API
    const BATCH_SIZE = 5;
    let processedInReport = 0;
    
    for (let i = 0; i < trackChunk.length; i += BATCH_SIZE) {
      const batch = trackChunk.slice(i, i + BATCH_SIZE);
      
      // Process each track in the batch
      const batchPromises = batch.map(async (track) => {
        try {
          const result = await queryEASForTrack(track);
          
          if (result.found) {
            // Send match back to main thread
            parentPort.postMessage({
              type: 'match',
              data: {
                trackId: track.trackId,
                title: track.title,
                artist: track.artist,
                publisher: track.publisher,
                attestationUID: result.attestationUID,
                attester: result.attester,
                timeCreated: result.timeCreated,
                onChainData: result.onChainData
              }
            });
          }
          return result.found ? 1 : 0;
        } catch (error) {
          console.error(`Worker ${workerId} - Error processing track ${track.trackId}:`, error.message);
          return 0;
        }
      });
      
      // Wait for all tracks in this batch to complete
      await Promise.all(batchPromises);
      
      // Report progress periodically (not for every single track)
      processedInReport += batch.length;
      if (processedInReport >= 20 || i + BATCH_SIZE >= trackChunk.length) {
        parentPort.postMessage({
          type: 'progress',
          processed: processedInReport
        });
        processedInReport = 0;
      }
      
      // Add a small delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  async function queryEASForTrack(track) {
    try {
      const trackHash = createTrackHash(track);
      
      // Real EAS GraphQL query
      const query = `
        query GetAttestationsBySchema($schema: String!) {
          attestations(where: {
            schemaId: { equals: $schema }
          }, order: { timeCreated: DESC }, limit: 100) {
            id
            attester
            recipient
            revocable
            revocationTime
            timeCreated
            expirationTime
            data
          }
        }
      `;
      
      const variables = {
        schema: MUSIC_SCHEMA_UID
      };
      
      // Make the actual API call to EAS
      const response = await axios.post(EAS_GRAPHQL_URL, {
        query,
        variables
      });
      
      // Check for attestations that match our track hash
      const attestations = response.data?.data?.attestations || [];
      
      // We need to manually filter since EAS GraphQL doesn't support complex queries
      // For a real implementation, you'd need to decode the attestation data
      // based on your schema format and then compare with the track hash
      for (const attestation of attestations) {
        try {
          // Simplified check: convert the track hash to hex and check if it's in the data
          // In a real implementation, you'd decode the data according to your schema
          if (attestation.data && attestation.data.includes(trackHash)) {
            return {
              found: true,
              attestationUID: attestation.id,
              attester: attestation.attester,
              timeCreated: new Date(parseInt(attestation.timeCreated) * 1000).toISOString(),
              onChainData: {
                title: track.title, 
                artist: track.artist,
                publisher: track.publisher,
                hash: trackHash,
                matchType: "EAS On-Chain Attestation"
              }
            };
          }
        } catch (e) {
          // Continue to next attestation if there's an error parsing this one
          continue;
        }
      }
      
      // No match found
      return { found: false };
    } catch (error) {
      // If API fails, log error and return no match
      console.error(`Error querying EAS for ${track.title}:`, error.message);
      return { found: false, error: error.message };
    }
  }
  
  function createTrackHash(track) {
    // Create a normalized string from track data
    const normalizedData = `${track.title.toLowerCase()}:${track.artist.toLowerCase()}:${(track.publisher || '').toLowerCase()}`;
    
    // Create SHA-256 hash
    return crypto.createHash('sha256').update(normalizedData).digest('hex');
  }
  
  workerMain().catch(error => {
    console.error(`Worker ${workerData.workerId} error:`, error);
    process.exit(1);
  });
} 