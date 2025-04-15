/**
 * MESA AI Guardian - CSV Analyzer
 * 
 * This module analyzes music catalog CSV files to extract attestable claims
 * and identify rights information.
 */

const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');

// AI-based confidence thresholds
const CONFIDENCE_THRESHOLDS = {
  HIGH: 0.85,
  MEDIUM: 0.65,
  LOW: 0.45
};

// Rights type classification patterns
const RIGHTS_PATTERNS = {
  MASTER_RECORDING: ['master', 'recording', 'sound recording', 'master rights', 'sr'],
  COMPOSITION: ['composition', 'musical work', 'songwriter', 'publishing', 'writer', 'pa'],
  PERFORMANCE: ['performance', 'performing', 'neighboring rights', 'pr'],
  SYNC: ['sync', 'synchronization', 'visual media', 'film', 'tv'],
  MECHANICAL: ['mechanical', 'reproduction', 'distribution', 'stream']
};

/**
 * Analyzes a music catalog CSV file and extracts attestable claims
 * 
 * @param {string} filePath - Path to the CSV file
 * @returns {Promise<Array>} - Array of attestable claims with metadata
 */
async function analyzeCSV(filePath) {
  return new Promise((resolve, reject) => {
    const results = [];
    
    console.log(`AI Guardian: Analyzing catalog file ${filePath}`);
    
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', (data) => results.push(data))
      .on('end', () => {
        try {
          const analysis = processResults(results);
          console.log(`AI Guardian: Analysis complete. Found ${analysis.claims.length} attestable claims.`);
          resolve(analysis);
        } catch (error) {
          reject(error);
        }
      })
      .on('error', (error) => {
        reject(error);
      });
  });
}

/**
 * Processes CSV results to extract attestable claims
 * 
 * @param {Array} results - Raw CSV data rows
 * @returns {Object} - Analysis results with claims and metadata
 */
function processResults(results) {
  // Skip processing if no data
  if (!results || results.length === 0) {
    return { claims: [], metadata: { format: 'unknown', count: 0 } };
  }
  
  // Detect CSV format (ASCAP, BMI, custom, etc.)
  const format = detectFormat(results[0]);
  
  // Extract claims based on format
  const claims = extractClaims(results, format);
  
  // Analyze for conflicts and duplicates
  const conflicts = detectConflicts(claims);
  
  // Determine schema recommendations
  const schemaRecommendations = recommendSchemas(claims);
  
  return {
    claims,
    metadata: {
      format,
      count: results.length,
      uniqueArtists: countUniqueValues(claims, 'artist'),
      uniqueTitles: countUniqueValues(claims, 'title')
    },
    conflicts,
    schemaRecommendations
  };
}

/**
 * Detects the format of the CSV based on header columns
 * 
 * @param {Object} firstRow - First row of CSV data
 * @returns {string} - Detected format name
 */
function detectFormat(firstRow) {
  const columns = Object.keys(firstRow).map(key => key.toLowerCase());
  
  if (columns.includes('isrc') && columns.includes('title')) {
    if (columns.includes('society') || columns.includes('cae/ipi')) {
      return 'ASCAP';
    } else if (columns.includes('bmi_work_id')) {
      return 'BMI';
    } else if (columns.includes('artist') && columns.includes('upc')) {
      return 'LABEL';
    }
  }
  
  // Custom format detection using AI-like logic
  // In a real implementation, this would use NLP or similar approaches
  const columnsString = columns.join(' ');
  if (columnsString.includes('work') && columnsString.match(/title|name/)) {
    return 'PUBLISHER';
  }
  
  return 'CUSTOM';
}

/**
 * Extracts attestable claims from CSV rows based on detected format
 * 
 * @param {Array} rows - CSV data rows
 * @param {string} format - Detected format
 * @returns {Array} - Extracted claims with confidence scores
 */
function extractClaims(rows, format) {
  return rows.map(row => {
    // Create a base claim structure
    const claim = {
      title: extractField(row, ['title', 'work_title', 'work name', 'song title', 'track title']),
      artist: extractField(row, ['artist', 'performer', 'author', 'writer', 'band']),
      iswc: extractField(row, ['iswc', 'iwsc_code', 'international_code']),
      isrc: extractField(row, ['isrc', 'isrc_code', 'recording_code']),
      publisher: extractField(row, ['publisher', 'publishing', 'company', 'label']),
      publisherShare: extractPercentage(row, ['publisher_share', 'pub_share', 'pub%', 'publisher %']),
      writerShare: extractPercentage(row, ['writer_share', 'composer_share', 'writer %', 'writer%']),
      rightsType: determineRightsType(row),
      territory: extractTerritory(row),
      // Confidence represents AI's certainty about this claim
      confidence: calculateConfidence(row, format),
      format: format,
      raw: row // Keep the raw data for reference
    };
    
    return claim;
  }).filter(claim => claim.confidence > CONFIDENCE_THRESHOLDS.LOW);
}

/**
 * Extracts a field from a row using multiple possible column names
 * 
 * @param {Object} row - CSV row
 * @param {Array} possibleColumns - Possible column names
 * @returns {string} - Extracted value or null
 */
function extractField(row, possibleColumns) {
  for (const colName of possibleColumns) {
    // Check for exact match
    if (row[colName] !== undefined && row[colName] !== null && row[colName] !== '') {
      return row[colName];
    }
    
    // Check for case-insensitive match
    const matchingKey = Object.keys(row).find(key => 
      key.toLowerCase() === colName.toLowerCase());
    
    if (matchingKey && row[matchingKey] !== undefined && row[matchingKey] !== '') {
      return row[matchingKey];
    }
  }
  
  return null;
}

/**
 * Extracts a percentage value from a row
 * 
 * @param {Object} row - CSV row
 * @param {Array} possibleColumns - Possible column names
 * @returns {number} - Extracted percentage or null
 */
function extractPercentage(row, possibleColumns) {
  const rawValue = extractField(row, possibleColumns);
  if (!rawValue) return null;
  
  // Handle percent sign and convert to number
  let value = rawValue;
  if (typeof value === 'string') {
    value = value.replace(/%/g, '').trim();
  }
  
  const numValue = parseFloat(value);
  return isNaN(numValue) ? null : numValue;
}

/**
 * Determines the rights type from a row
 * 
 * @param {Object} row - CSV row
 * @returns {string} - Detected rights type
 */
function determineRightsType(row) {
  // Convert row to string for pattern matching
  const rowString = JSON.stringify(row).toLowerCase();
  
  // Check each rights pattern
  for (const [rightsType, patterns] of Object.entries(RIGHTS_PATTERNS)) {
    for (const pattern of patterns) {
      if (rowString.includes(pattern.toLowerCase())) {
        return rightsType;
      }
    }
  }
  
  // Default to composition if artist and publisher are present
  if (extractField(row, ['artist', 'writer']) && 
      extractField(row, ['publisher'])) {
    return 'COMPOSITION';
  }
  
  // Default to master recording if artist and label are present
  if (extractField(row, ['artist', 'performer']) && 
      extractField(row, ['label'])) {
    return 'MASTER_RECORDING';
  }
  
  return 'UNKNOWN';
}

/**
 * Extracts territory information from a row
 * 
 * @param {Object} row - CSV row
 * @returns {string} - Territory code
 */
function extractTerritory(row) {
  const territoryField = extractField(row, [
    'territory', 'region', 'country', 'coverage', 'countries'
  ]);
  
  if (territoryField) {
    return territoryField;
  }
  
  // Default to worldwide
  return 'WW';
}

/**
 * Calculates confidence score for a claim
 * 
 * @param {Object} row - CSV row
 * @param {string} format - Detected format
 * @returns {number} - Confidence score between 0 and 1
 */
function calculateConfidence(row, format) {
  let score = 0;
  
  // Title and artist are crucial
  if (extractField(row, ['title', 'work_title', 'song title'])) score += 0.3;
  if (extractField(row, ['artist', 'performer', 'writer'])) score += 0.3;
  
  // Rights identifiers boost confidence
  if (extractField(row, ['iswc'])) score += 0.15;
  if (extractField(row, ['isrc'])) score += 0.15;
  
  // Rights holder information 
  if (extractField(row, ['publisher', 'label', 'company'])) score += 0.1;
  
  // Known formats get a slight boost
  if (format !== 'CUSTOM') score += 0.05;
  
  // Cap at 1.0
  return Math.min(score, 1.0);
}

/**
 * Detects potential conflicts and duplicates in claims
 * 
 * @param {Array} claims - Processed claims
 * @returns {Array} - Detected conflicts
 */
function detectConflicts(claims) {
  const conflicts = [];
  const titleArtistMap = new Map();
  
  claims.forEach((claim, index) => {
    if (!claim.title || !claim.artist) return;
    
    const key = `${claim.title.toLowerCase()}-${claim.artist.toLowerCase()}`;
    
    if (titleArtistMap.has(key)) {
      const existingIndex = titleArtistMap.get(key);
      const existing = claims[existingIndex];
      
      // Check for ownership conflicts
      if (existing.publisher !== claim.publisher) {
        conflicts.push({
          type: 'PUBLISHER_CONFLICT',
          claim1Index: existingIndex,
          claim2Index: index,
          description: `Conflicting publishers for "${claim.title}" by ${claim.artist}`
        });
      }
      
      // Check for rights type conflicts
      if (existing.rightsType !== claim.rightsType && 
          existing.rightsType !== 'UNKNOWN' && 
          claim.rightsType !== 'UNKNOWN') {
        conflicts.push({
          type: 'RIGHTS_TYPE_CONFLICT',
          claim1Index: existingIndex,
          claim2Index: index,
          description: `Conflicting rights types for "${claim.title}" by ${claim.artist}`
        });
      }
    } else {
      titleArtistMap.set(key, index);
    }
  });
  
  return conflicts;
}

/**
 * Recommends schemas based on the analyzed claims
 * 
 * @param {Array} claims - Processed claims
 * @returns {Object} - Schema recommendations
 */
function recommendSchemas(claims) {
  // Count the different rights types
  const typeCount = claims.reduce((counts, claim) => {
    counts[claim.rightsType] = (counts[claim.rightsType] || 0) + 1;
    return counts;
  }, {});
  
  // Determine if we need separate schemas or can use a unified one
  const needsMultipleSchemas = 
    Object.keys(typeCount).length > 1 && 
    !typeCount.UNKNOWN;
  
  if (needsMultipleSchemas) {
    return {
      recommendation: 'MULTIPLE',
      schemas: Object.keys(typeCount).map(type => ({
        type,
        name: `${type.toLowerCase()}_rights`,
        count: typeCount[type],
        fields: getSchemaFieldsForType(type)
      }))
    };
  } else {
    return {
      recommendation: 'SINGLE',
      schema: {
        name: 'music_rights',
        fields: getSchemaFieldsForType('UNIVERSAL')
      }
    };
  }
}

/**
 * Gets schema fields based on rights type
 * 
 * @param {string} type - Rights type
 * @returns {Array} - Schema field definitions
 */
function getSchemaFieldsForType(type) {
  const baseFields = [
    'string title',
    'string artist',
    'address rightsHolder'
  ];
  
  switch (type) {
    case 'MASTER_RECORDING':
      return [
        ...baseFields,
        'string isrc',
        'string label',
        'uint256 releaseYear'
      ];
    case 'COMPOSITION':
      return [
        ...baseFields,
        'string iswc',
        'string publisher',
        'uint8 writerShare',
        'uint8 publisherShare'
      ];
    case 'PERFORMANCE':
      return [
        ...baseFields,
        'string venue',
        'uint256 performanceDate'
      ];
    case 'SYNC':
      return [
        ...baseFields,
        'string mediaTitle',
        'string licenseType'
      ];
    case 'UNIVERSAL':
    default:
      return [
        ...baseFields,
        'string iswc',
        'string isrc',
        'string rightsType',
        'string territory'
      ];
  }
}

/**
 * Counts unique values in a specific claim field
 * 
 * @param {Array} claims - Processed claims
 * @param {string} field - Field to count unique values for
 * @returns {number} - Count of unique values
 */
function countUniqueValues(claims, field) {
  const values = new Set();
  
  claims.forEach(claim => {
    if (claim[field]) {
      values.add(claim[field].toLowerCase());
    }
  });
  
  return values.size;
}

module.exports = {
  analyzeCSV,
  calculateConfidence,
  detectConflicts,
  recommendSchemas,
  CONFIDENCE_THRESHOLDS
}; 