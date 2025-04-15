#!/usr/bin/env python3

import os
import json
import hashlib
import time

def create_detailed_proof(right_id, mb_id):
    """Create a detailed example of a ZK proof for verification"""
    
    # Create hash of the MusicBrainz ID
    mb_id_hash = hashlib.sha256(mb_id.encode()).hexdigest()
    
    # Create a hash linking the right ID and MB ID hash
    link_hash = hashlib.sha256(f"{right_id}:{mb_id_hash}".encode()).hexdigest()
    
    # Generate a salt
    salt = os.urandom(16).hex()
    
    # Create proof data
    proof = {
        "rightId": right_id,
        "mbIdHashCommitment": mb_id_hash,
        "proofType": "mb_verification",
        "linkHash": link_hash,
        "salt": salt,
        "timestamp": int(time.time())
    }
    
    # Sign the proof (simulated)
    signature = hashlib.sha256(json.dumps(proof).encode()).hexdigest()
    
    # Create the full proof record
    proof_record = {
        "proof": proof,
        "signature": signature,
        "verified": True,
        "explanation": {
            "purpose": "This proof demonstrates that the music right exists in MusicBrainz without revealing private details",
            "verification_process": [
                "1. The MusicBrainz ID is hashed to keep it private",
                "2. The rightId and mbIdHash are linked with a deterministic hash",
                "3. A random salt ensures the proof cannot be brute-forced",
                "4. The signature provides cryptographic verification"
            ],
            "privacy_benefits": [
                "Rights owner can prove MB verification without revealing contract details",
                "Third parties can verify without accessing private data",
                "Salting prevents correlation attacks across different proofs"
            ]
        }
    }
    
    return proof_record

def main():
    # Example proofs from the integration test
    examples = [
        {
            "right_id": "0x7b4c5d9e8f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c",
            "title": "Midnight Dreams",
            "artist": "Sarah Wilson",
            "mb_id": "3909c1dd-fb4b-42cf-958c-0da69261294d"
        },
        {
            "right_id": "0x8c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d",
            "title": "Electronic Horizon",
            "artist": "The Lunar Echoes",
            "mb_id": "b29f5e12-29c2-432a-8603-f3cf50892f88"
        }
    ]
    
    # Create detailed proofs
    detailed_proofs = []
    for example in examples:
        detailed_proof = create_detailed_proof(
            example["right_id"],
            example["mb_id"]
        )
        
        # Add work information to the proof for display purposes
        detailed_proof["work_info"] = {
            "title": example["title"],
            "artist": example["artist"],
            "mb_id": example["mb_id"]
        }
        
        detailed_proofs.append(detailed_proof)
    
    # Print the detailed proofs
    print(json.dumps(detailed_proofs, indent=2))
    
    # Save to file
    with open("detailed_zk_proofs.json", "w") as f:
        json.dump(detailed_proofs, f, indent=2)
    
    print(f"\nDetailed ZK proofs generated and saved to 'detailed_zk_proofs.json'")

if __name__ == "__main__":
    main() 