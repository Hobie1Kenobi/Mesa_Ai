# MESA Rights Vault - Quick Start Guide

This guide will help you quickly understand and run the MESA Rights Vault system. It's designed for new team members to get up and running fast.

## What is MESA Rights Vault?

MESA Rights Vault is a privacy-focused music rights management system built on the Base blockchain. It allows artists to:

- Store and manage their music rights securely
- Share only the information they choose to share
- Verify their rights without revealing sensitive details
- Connect rights data to music industry databases like MusicBrainz

## System Requirements

- Python 3.8 or higher
- Node.js 14 or higher
- Git
- Access to Base Sepolia testnet (for blockchain interactions)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/mesa/rights-vault.git
cd rights-vault
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs key packages like:
- web3
- cryptography
- requests
- numpy

### 3. Set Up Environment Variables

Create a `.env` file in the root directory:

```
# API Keys
MUSICBRAINZ_API_KEY=your_key_here
BASE_RPC_URL=https://sepolia.base.org

# Contract Addresses
RIGHTS_VAULT_ADDRESS=0x7338af1E9d6dbc4cc1Efa067C0775Bf222aDb0C3

# Private Keys (NEVER share these or commit to git)
WALLET_PRIVATE_KEY=your_private_key_here
```

### 4. Run the Demo Components

#### Test MusicBrainz Integration

```bash
cd ai_guardian/data/training
python musicbrainz_integration_test.py
```

This will:
- Connect to MusicBrainz API
- Test lookup and verification
- Generate sample proofs
- Show privacy-preserving data storage

#### Generate and Verify Proofs

```bash
# Generate detailed proofs
python show_proof.py

# Verify proofs and show selective disclosure
python verify_proof.py --reveal
```

## Key Components Overview

### Smart Contracts

Located in `ai_guardian/contracts/`:
- `RightsVault.sol` - Core contract for encrypted storage
- `MusicRightsVault.sol` - Music-specific rights management

### Privacy System

Located in `ai_guardian/scripts/`:
- `zk_proofs.py` - Zero-knowledge proof generation
- `privacy_layer.py` - Encryption and privacy controls

### AI Components

Located in `ai_guardian/src/`:
- `rights_guardian.py` - Rights extraction from documents
- `integration_demo.py` - Demo of the entire system workflow

### Training Data

Located in `ai_guardian/data/training/`:
- Schema definitions
- Sample music rights data
- Training materials for ZK proofs

## Common Tasks

### Adding a New Music Right

1. Prepare the right data (in JSON format)
2. Use the privacy layer to encrypt sensitive fields
3. Generate a unique ID for the right
4. Create transaction for blockchain storage

Example:
```python
from privacy_layer import PrivacyLayer
from rights_guardian import RightsGuardian

# Initialize components
privacy = PrivacyLayer()
guardian = RightsGuardian()

# Create a new right
right_data = {
    "workTitle": "My Amazing Song",
    "artistParty": "Talented Artist",
    "rightsType": "Publishing",
    "territory": "Global",
    "term": "5 years",
    "royaltyInfo": [{"party": "Artist", "percentage": 0.7},
                     {"party": "Publisher", "percentage": 0.3}]
}

# Process for blockchain storage
encrypted_data = privacy.encrypt_entity(right_data)
blockchain_tx = guardian.prepare_for_blockchain(right_data)

# The data is now ready to send to the blockchain
```

### Verifying a Music Right

1. Get the right ID to verify
2. Request a zero-knowledge proof
3. Verify the proof without seeing the sensitive data

Example:
```python
from zk_proofs import ZKProofSystem

# Initialize the ZK system
zk = ZKProofSystem()

# Create an ownership proof
right_id = "0x7b4c5d9e8f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c"
rights_type = "Publishing"
owner_address = "0x123..."

proof = zk.create_ownership_proof(right_id, rights_type, owner_address)

# Verify the proof (could be done by a third party)
is_valid = zk.verify_ownership_proof(proof)
print(f"Proof valid: {is_valid}")
```

## Troubleshooting

### Cannot Connect to MusicBrainz API

Check your rate limiting - MusicBrainz limits to 1 request per second.

Solution: Add `time.sleep(1)` between requests.

### ZK Proof Verification Fails

Common causes:
- Incorrect salt or hash parameters
- Proof format mismatch
- Wrong signature verification

Solution: Check the proof generation parameters match verification parameters.

### Blockchain Transaction Fails

Common causes:
- Insufficient gas
- Wrong contract address
- Network issues

Solution: Use simulation mode for testing:
```python
# Set simulation mode to test without blockchain
os.environ["SIMULATION_MODE"] = "True"
```

## Next Steps

After getting familiar with the system:

1. Run the full training pipeline: `python training_script.py`
2. Examine the training data and ZK circuit templates
3. Try modifying the selective disclosure settings
4. Explore MusicBrainz integration with your own music samples

## Resources

- Full documentation: `docs/` directory
- System architecture: `project_diagram.md`
- Code examples: `examples/` directory

## Support

If you have questions, contact the MESA team at:
- Email: team@mesarightsvault.com
- Slack: #mesa-rights-vault channel 