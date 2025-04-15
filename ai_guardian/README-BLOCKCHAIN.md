# MESA AI Guardian - Blockchain Rights Verification

This tool integrates the ASCAP database analysis with Ethereum Attestation Service (EAS) on Base Sepolia to verify music rights and detect potential issues.

## Overview

The MESA AI Guardian provides:

1. **Rights Analysis**: Analyzes music catalog data to identify potential rights issues:
   - Tracks with multiple artists that may have complex rights structures
   - Suspicious titles indicating sampling or derivative works
   - Metadata inconsistencies across different sources

2. **Blockchain Verification**: Checks if rights have been registered on-chain:
   - Creates cryptographic hashes from track metadata for lookup
   - Queries the EAS blockchain for matching attestations
   - Records matches between catalog data and on-chain attestations

3. **Output Reports**: Generates CSV reports for:
   - Issues detected in the music catalog
   - On-chain attestation matches with detailed attestation data

## Getting Started

### Prerequisites

- Node.js 16 or higher
- A CSV file containing music tracks (like ASCAP data)

### Installation

1. Install dependencies:
   ```bash
   npm install ethers@5.7.2 axios dotenv
   ```

2. Set up environment variables in `.env`:
   ```
   # EAS Blockchain Settings
   EAS_CONTRACT_ADDRESS=0xC2679fBD37d54388Ce493F1DB75320D236e1815e
   SCHEMA_REGISTRY_ADDRESS=0x0a7E2Ff54e76B8E6659aedc9103FB21c038050D0
   RPC_URL=https://sepolia.base.org
   MUSIC_SCHEMA_UID=0x0d8026ba54409df0a7ecf71c9e0a29e8f2faaf3ea12b138d0a0c1ecf69c7ca98
   ```

### Usage

Run the analysis on your music catalog:

```bash
node eas-direct-integration.js analyze <csv-file> [batch-size] [limit]
```

Parameters:
- `csv-file`: Path to the CSV file containing track data
- `batch-size`: (Optional) Number of tracks to process in each batch (default: 100)
- `limit`: (Optional) Maximum number of tracks to process (default: all)

Example:
```bash
node eas-direct-integration.js analyze MESA_DEMO_CATALOG.csv 10 100
```

## Sample Output

The tool generates two CSV files in the `analysis_results` directory:

### 1. `issues_detected.csv`
Lists tracks with potential rights issues:
```
TrackId,Title,Artist,Publisher,IssueType,IssueDetails
unknown-1,Midnight Dreams,Sophia Chen,Evergreen Music Publishing,MultipleArtists,Multiple artists may have rights conflicts
unknown-3,Skyward,Marcus Lee,Evergreen Music Publishing,MultipleArtists,Multiple artists may have rights conflicts
```

### 2. `blockchain_matches.csv`
Lists tracks that match on-chain attestations:
```
TrackId,Title,Artist,Publisher,AttestationUID,Attester,TimeCreated,OnChainData
unknown-5,Autumn Leaves Fall,The Seasons,Unknown,0x62567ef5730af48e...,0xd57295fc9b5a1,2025-04-14T22:52:58.355Z,{"title":"Autumn Leaves Fall","artist":"The Seasons",...}
```

## Full Blockchain Integration

The current implementation provides a simulation of blockchain integration. For full integration with EAS:

1. Create a rights schema on Base Sepolia using `create_eas_attestation.js`
2. Use the EAS GraphQL API for real attestation queries
3. Add your private key to the `.env` file if you need to create attestations

## Adding Your Own Data

To analyze your own music catalog:
1. Format your data as a CSV with headers
2. Ensure it has at least title and artist information
3. Run the analysis script on your CSV file

## Next Steps

- Implement full GraphQL query integration with EAS
- Add direct attestation creation from the tool
- Develop a validation module to compare on-chain and off-chain data 