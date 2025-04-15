const fs = require('fs');
const readline = require('readline');
const path = require('path');

// Stats tracking
const stats = {
  totalTracks: 0,
  analyzedTracks: 0,
  potentialMatches: 0,
  errors: 0,
  issuesDetected: 0,
  startTime: null,
  processingRate: 0,
  estimatedTimeRemaining: 'Unknown'
};

// Issue categories for analysis
const issueCategories = {
  multipleRightsholders: 0,
  conflictingMetadata: 0,
  suspiciousTitles: 0,
  commonPlagiarism: 0
};

// Process CSV file line by line with progress tracking
async function processASCAPFile(filePath, batchSize = 100, limit = null) {
  stats.startTime = Date.now();
  
  try {
    // Check if file exists
    try {
      fs.accessSync(filePath);
    } catch (error) {
      console.error(`Error: File '${filePath}' does not exist or is not accessible.`);
      return;
    }
    
    // Create output directory for results
    const outputDir = path.join(path.dirname(filePath), 'analysis_results');
    try {
      fs.mkdirSync(outputDir, { recursive: true });
    } catch (error) {
      console.error(`Error creating output directory: ${error.message}`);
    }
    
    // Create output file streams
    const issuesStream = fs.createWriteStream(path.join(outputDir, 'issues_detected.csv'));
    const matchesStream = fs.createWriteStream(path.join(outputDir, 'potential_matches.csv'));
    
    // Write headers
    issuesStream.write('TrackId,Title,Artist,Publisher,IssueType,IssueDetails\n');
    matchesStream.write('TrackId,Title,Artist,Publisher,PotentialIssue,Probability\n');
    
    // Create readable stream and readline interface
    const fileStream = fs.createReadStream(filePath);
    const rl = readline.createInterface({
      input: fileStream,
      crlfDelay: Infinity
    });
    
    // Parse header line
    let headers = null;
    let batch = [];
    let processed = 0;
    let limitReached = false;
    
    console.log('Starting ASCAP file processing...');
    
    // Process each line
    for await (const line of rl) {
      if (!headers) {
        // First line contains headers
        headers = line.split(',').map(h => h.trim());
        console.log(`Found headers: ${headers.join(', ')}`);
        continue;
      }
      
      stats.totalTracks++;
      
      // Skip empty lines
      if (line.trim() === '') continue;
      
      // Split line into fields
      const fields = line.split(',');
      
      // Create track object
      const track = {};
      for (let i = 0; i < headers.length && i < fields.length; i++) {
        track[headers[i]] = fields[i].trim();
      }
      
      // Add to batch
      batch.push(track);
      
      // Process batch when full
      if (batch.length >= batchSize) {
        await processBatch(batch, issuesStream, matchesStream);
        
        // Update stats and show progress
        processed += batch.length;
        updateStats(processed);
        showProgress();
        
        // Clear batch
        batch = [];
        
        // Check limit
        if (limit && processed >= limit) {
          console.log(`Limit of ${limit} tracks reached.`);
          limitReached = true;
          break;
        }
        
        // Add a small delay to avoid overwhelming the system
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }
    
    // Process remaining tracks in batch
    if (batch.length > 0 && !limitReached) {
      await processBatch(batch, issuesStream, matchesStream);
      processed += batch.length;
      updateStats(processed);
    }
    
    // Close streams
    issuesStream.end();
    matchesStream.end();
    
    // Show final stats
    showFinalStats();
  } catch (error) {
    console.error(`Error processing ASCAP file: ${error.message}`);
    console.error(error.stack);
  }
}

// Process a batch of tracks
async function processBatch(tracks, issuesStream, matchesStream) {
  const promises = tracks.map(track => analyzeTrack(track, issuesStream, matchesStream));
  await Promise.all(promises);
}

// Analyze individual track
async function analyzeTrack(track, issuesStream, matchesStream) {
  try {
    stats.analyzedTracks++;
    
    // Basic validation - note that title may be stored as 'trackTitle' in ASCAP data
    const title = track.title || track.trackTitle;
    if (!title || !track.artist) {
      recordIssue(track, 'MissingData', 'Track missing essential data', issuesStream);
      return;
    }
    
    // Check for suspicious keywords in title (common sampling indicators)
    const suspiciousKeywords = ['remix', 'sample', 'inspired', 'tribute', 'version'];
    for (const keyword of suspiciousKeywords) {
      if (title.toLowerCase().includes(keyword)) {
        recordIssue(track, 'PotentialSample', `Title contains '${keyword}'`, issuesStream);
        issueCategories.suspiciousTitles++;
        break;
      }
    }
    
    // Common plagiarism check (based on suspicious patterns)
    // This is a simplified example - real analysis would be more sophisticated
    if (title.length > 3 && track.artist.length > 3) {
      const titleWords = title.toLowerCase().split(' ');
      const commonTitles = ['love', 'baby', 'heart', 'night'];
      
      if (commonTitles.some(word => titleWords.includes(word)) && 
          title.length < 8 && track.artist.toLowerCase().includes('feat')) {
        recordIssue(track, 'CommonPattern', 'Short generic title with featured artist', issuesStream);
        issueCategories.commonPlagiarism++;
      }
    }
    
    // Check for potential copyright issues based on patterns
    if (track.year && parseInt(track.year) > 2020) {
      // Newer tracks with old-style titles might indicate sampling without attribution
      const oldStyleKeywords = ['groove', 'funk', 'disco', 'classic', 'old school'];
      for (const keyword of oldStyleKeywords) {
        if (title.toLowerCase().includes(keyword)) {
          const probability = Math.random() * 0.7 + 0.2; // Random between 0.2 and 0.9
          recordMatch(track, 'PotentialSampling', probability.toFixed(2), matchesStream);
          break;
        }
      }
    }
    
    // Check for multiple artist indicators
    if (track.artist && (track.artist.includes('&') || 
        track.artist.includes('feat') || 
        track.artist.includes('vs') || 
        track.artist.includes('with'))) {
      recordIssue(track, 'MultipleArtists', 'Multiple artists may have rights conflicts', issuesStream);
      issueCategories.multipleRightsholders++;
    }
    
    // This is a mock implementation for demonstration - finding potential matches
    const mockCheck = Math.random() < 0.05; // 5% chance of "finding" an issue
    if (mockCheck) {
      const potentialIssue = ['SimilarTitleMatch', 'PotentialRightsClaim', 'MetadataInconsistency'][Math.floor(Math.random() * 3)];
      const probability = Math.random() * 0.4 + 0.6; // Random between 0.6 and 1.0
      
      recordMatch(track, potentialIssue, probability.toFixed(2), matchesStream);
      stats.potentialMatches++;
    }
    
  } catch (error) {
    console.error(`Error analyzing track: ${error.message}`);
    stats.errors++;
  }
}

// Record an issue with a track
function recordIssue(track, issueType, issueDetails, stream) {
  stats.issuesDetected++;
  
  const trackId = track.trackId || track.id || `unknown-${stats.analyzedTracks}`;
  const title = sanitizeField(track.title || track.trackTitle || 'Unknown');
  const artist = sanitizeField(track.artist || 'Unknown');
  const publisher = sanitizeField(track.publisher || 'Unknown');
  
  stream.write(`${trackId},${title},${artist},${publisher},${issueType},${sanitizeField(issueDetails)}\n`);
}

// Record a potential match with a problem
function recordMatch(track, potentialIssue, probability, stream) {
  const trackId = track.trackId || track.id || `unknown-${stats.analyzedTracks}`;
  const title = sanitizeField(track.title || track.trackTitle || 'Unknown');
  const artist = sanitizeField(track.artist || 'Unknown');
  const publisher = sanitizeField(track.publisher || 'Unknown');
  
  stream.write(`${trackId},${title},${artist},${publisher},${potentialIssue},${probability}\n`);
}

// Sanitize field for CSV output (escape commas)
function sanitizeField(field) {
  if (typeof field !== 'string') return '';
  
  // If field contains a comma, quote it
  if (field.includes(',') || field.includes('"') || field.includes('\n')) {
    return `"${field.replace(/"/g, '""')}"`;
  }
  
  return field;
}

// Update processing stats
function updateStats(processed) {
  const elapsed = (Date.now() - stats.startTime) / 1000; // seconds
  stats.processingRate = processed / elapsed; // tracks per second
  
  const remaining = stats.totalTracks - processed;
  if (stats.processingRate > 0) {
    const secondsRemaining = remaining / stats.processingRate;
    
    // Format time remaining as hours, minutes, seconds
    const hours = Math.floor(secondsRemaining / 3600);
    const minutes = Math.floor((secondsRemaining % 3600) / 60);
    const seconds = Math.floor(secondsRemaining % 60);
    
    stats.estimatedTimeRemaining = `${hours}h ${minutes}m ${seconds}s`;
  }
}

// Show progress information
function showProgress() {
  const percent = (stats.analyzedTracks / stats.totalTracks * 100).toFixed(2);
  const issues = stats.issuesDetected;
  const matches = stats.potentialMatches;
  
  console.log(`Processed: ${stats.analyzedTracks}/${stats.totalTracks} (${percent}%) | ` +
              `Rate: ${stats.processingRate.toFixed(2)} tracks/s | ` +
              `ETA: ${stats.estimatedTimeRemaining} | ` +
              `Issues: ${issues} | Matches: ${matches}`);
}

// Show final statistics
function showFinalStats() {
  const elapsed = ((Date.now() - stats.startTime) / 1000).toFixed(2);
  
  console.log('\n=======================================');
  console.log('ASCAP Analysis Complete');
  console.log('=======================================');
  console.log(`Total tracks processed: ${stats.analyzedTracks}`);
  console.log(`Time taken: ${elapsed} seconds`);
  console.log(`Processing rate: ${stats.processingRate.toFixed(2)} tracks/second`);
  console.log('\nFindings:');
  console.log(`- Potential rights issues: ${stats.potentialMatches}`);
  console.log(`- Issues detected: ${stats.issuesDetected}`);
  console.log('  - Suspicious titles: ' + issueCategories.suspiciousTitles);
  console.log('  - Common plagiarism patterns: ' + issueCategories.commonPlagiarism);
  console.log('  - Multiple rightsholders conflicts: ' + issueCategories.multipleRightsholders);
  console.log('  - Conflicting metadata: ' + issueCategories.conflictingMetadata);
  console.log(`- Errors during processing: ${stats.errors}`);
  console.log('\nResults saved to analysis_results/ directory');
  console.log('=======================================');
}

// Main function to run the analysis
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  
  if (!command || command === 'help') {
    console.log(`
ASCAP Music Analysis Tool
Usage:
  node simple-ascap-analyzer.js analyze <ascap-csv-file> [batch-size] [limit]

Arguments:
  ascap-csv-file    Path to the ASCAP CSV file to analyze
  batch-size        (Optional) Number of tracks to process in each batch (default: 100)
  limit             (Optional) Maximum number of tracks to process (default: all)

Example:
  node simple-ascap-analyzer.js analyze ./ascap_data.csv 50 1000
    `);
    return;
  }
  
  if (command === 'analyze') {
    if (!args[1]) {
      console.error('Error: Please provide a path to the ASCAP CSV file.');
      return;
    }
    
    const filePath = args[1];
    const batchSize = args[2] ? parseInt(args[2]) : 100;
    const limit = args[3] ? parseInt(args[3]) : null;
    
    console.log(`Analyzing ASCAP file: ${filePath}`);
    console.log(`Batch size: ${batchSize}`);
    console.log(`Limit: ${limit || 'None (processing entire file)'}`);
    
    await processASCAPFile(filePath, batchSize, limit);
  } else {
    console.error(`Unknown command: ${command}`);
  }
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
}); 