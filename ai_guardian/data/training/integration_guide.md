# MusicBrainz Integration Guide for MESA Rights Vault

This guide describes how to integrate MusicBrainz data with the MESA Rights Vault platform for enhanced music rights management with privacy-preserving capabilities.

## Overview

MusicBrainz offers a comprehensive database of music metadata which can be leveraged to improve the accuracy and completeness of music rights data in the MESA Rights Vault. By connecting these systems, we can:

1. Verify the existence and details of musical works
2. Enrich rights data with standardized identifiers (ISWC, ISRC)
3. Validate artist and publisher information
4. Improve discoverability while maintaining privacy

## Data Mapping

| MusicBrainz Entity | MESA Rights Field | Notes |
|-------------------|-------------------|-------|
| Work.title | MusicRight.workTitle | Direct mapping |
| Work.iswc | MusicRight.identifiers.iswc | Standard identifier for compositions |
| Recording.isrc | MusicRight.identifiers.isrc | Standard identifier for recordings |
| Artist.name | MusicRight.artistParty | May require disambiguation |
| Label.name | MusicRight.publisherParty | Not all publishers are labels |
| Artist-Work Relationship | Royalty distribution | Composer credits can inform royalty splits |

## Integration Process

### 1. Initial Setup

1. Register for MusicBrainz API access at https://musicbrainz.org/account/register
2. Install the required libraries:
   ```bash
   pip install musicbrainzngs cryptography web3
   ```
3. Configure MusicBrainz API access in your application:
   ```python
   import musicbrainzngs
   
   musicbrainzngs.set_useragent(
       "MESA_Rights_Vault", 
       "0.1",
       "https://mesa-rights-vault.example.com"
   )
   ```

### 2. Lookup and Verification Process

When a user registers a music right, implement the following workflow:

1. Search MusicBrainz for matching works/recordings
2. Present potential matches to the user for confirmation
3. Upon confirmation, extract relevant identifiers and metadata
4. Hash and encrypt sensitive details for privacy protection
5. Store links to MusicBrainz IDs in a privacy-preserving way

Example Python code:

```python
def search_and_verify_work(work_title, artist_name):
    """Search MusicBrainz for a musical work and verify its existence"""
    # Search for works matching the title
    search_result = musicbrainzngs.search_works(work=work_title, artist=artist_name)
    
    if search_result['work-list']:
        works = search_result['work-list']
        return {
            'found': True,
            'matches': [
                {
                    'title': work['title'],
                    'id': work['id'],
                    'iswc': work.get('iswc', 'Unknown'),
                    'composers': [artist['name'] for artist in work.get('artist-relation-list', [])]
                }
                for work in works[:5]  # Return top 5 matches
            ]
        }
    return {'found': False}
```

### 3. Privacy-Preserving Storage

When storing verified MusicBrainz data, implement these privacy measures:

1. Create a one-way hash linking MESA rights entries to MusicBrainz IDs
2. Store complete MusicBrainz metadata in encrypted format
3. Use zero-knowledge proofs to verify data against MusicBrainz without revealing the actual data

Example storage approach:

```python
from cryptography.fernet import Fernet
import hashlib
import json

def store_musicbrainz_data(mesa_right_id, mb_data, encryption_key):
    """Store MusicBrainz data with privacy protection"""
    # Create a one-way hash of the MusicBrainz ID
    mb_id = mb_data['id']
    mb_id_hash = hashlib.sha256(mb_id.encode()).hexdigest()
    
    # Encrypt the full MusicBrainz data
    cipher = Fernet(encryption_key)
    encrypted_mb_data = cipher.encrypt(json.dumps(mb_data).encode())
    
    # Store the reference
    mbz_reference = {
        'mesa_right_id': mesa_right_id,
        'mb_id_hash': mb_id_hash,
        'encrypted_data': encrypted_mb_data.decode(),
        'timestamp': int(time.time())
    }
    
    # Save to database (implementation depends on your storage system)
    db.save_mbz_reference(mbz_reference)
    
    return mb_id_hash
```

### 4. Zero-Knowledge Proof Generation

Generate ZK proofs to verify rights information against MusicBrainz data:

```python
from zk_proofs import ZKProofSystem

def generate_mbz_verification_proof(mesa_right, mb_data_hash, encryption_key):
    """Generate a zero-knowledge proof that the right exists in MusicBrainz"""
    # Initialize the ZK proof system
    zk = ZKProofSystem()
    
    # Extract key identifiers
    work_id = mesa_right['workTitle']
    artist_name = mesa_right['artistParty']
    
    # Create a proof that links to MusicBrainz without revealing the actual IDs
    ownership_proof = zk.create_ownership_proof(
        work_id, 
        mesa_right['rightsType'],
        mesa_right['rightId']
    )
    
    return ownership_proof
```

## Selective Disclosure with MusicBrainz Data

When creating selective disclosure proofs for third parties:

1. Define standard disclosure templates for different use cases
2. Include appropriate MusicBrainz identifiers in templates
3. Generate proofs that reveal only the necessary information

Example of selective disclosure:

```python
def create_streaming_platform_disclosure(mesa_right, mb_data, encryption_key):
    """Create a disclosure proof for a streaming platform"""
    # Initialize privacy layer
    privacy = PrivacyLayer(master_key=encryption_key)
    
    # Define fields to disclose for streaming use case
    streaming_fields = [
        'workTitle', 
        'artistParty', 
        'rightsType', 
        'territory', 
        'identifiers.isrc'  # Include ISRC from MusicBrainz
    ]
    
    # Create combined data object with minimal MB data
    combined_data = {**mesa_right}
    if 'identifiers' not in combined_data:
        combined_data['identifiers'] = {}
    
    # Add only the necessary identifiers from MusicBrainz
    if 'isrc' in mb_data:
        combined_data['identifiers']['isrc'] = mb_data['isrc']
    
    # Generate the selective disclosure proof
    disclosure = privacy.create_disclosure_proof(
        combined_data,
        fields_to_disclose=streaming_fields
    )
    
    return disclosure
```

## Verification by Third Parties

Third parties can verify rights information against MusicBrainz without requiring access to the full MusicBrainz database:

1. Provide a verification API endpoint
2. Accept selective disclosure proofs and verification requests
3. Verify the proof cryptographically
4. Optionally check against MusicBrainz if authorized

## Best Practices

1. **Minimal Data Collection**: Only store MusicBrainz data essential for rights verification
2. **Regular Syncing**: Update links to MusicBrainz periodically to reflect changes
3. **User Consent**: Always get user permission before linking to external databases
4. **Transparent Controls**: Give users visibility into what data is being shared
5. **Audit Logging**: Maintain logs of all verification requests in a privacy-preserving way

## Resources

- [MusicBrainz API Documentation](https://musicbrainz.org/doc/MusicBrainz_API)
- [MusicBrainz Database Schema](https://musicbrainz.org/doc/MusicBrainz_Database/Schema)
- [MESA Rights Vault ZK Proof Documentation](https://example.com/docs/zk-proofs)
- [MESA Privacy Layer](https://example.com/docs/privacy-layer) 