#!/usr/bin/env python3

import json
import hashlib
import argparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ProofVerifier:
    """
    Verifies zero-knowledge proofs for MusicBrainz integration
    """
    
    def __init__(self):
        """Initialize the proof verifier"""
        pass
    
    def verify_proof(self, proof_data):
        """Verify a zero-knowledge proof"""
        # Extract proof components
        proof = proof_data.get("proof", {})
        signature = proof_data.get("signature", "")
        
        # Check if proof has all required fields
        required_fields = ["rightId", "mbIdHashCommitment", "proofType", "linkHash", "salt", "timestamp"]
        if not all(field in proof for field in required_fields):
            logging.error("Proof is missing required fields")
            return False
        
        # Verify proof type
        if proof.get("proofType") != "mb_verification":
            logging.error(f"Unsupported proof type: {proof.get('proofType')}")
            return False
        
        # Verify the signature
        calculated_signature = hashlib.sha256(json.dumps(proof).encode()).hexdigest()
        if calculated_signature != signature:
            logging.error("Signature verification failed")
            return False
        
        # Verify the link hash (relationship between rightId and mbIdHashCommitment)
        right_id = proof.get("rightId")
        mb_id_hash = proof.get("mbIdHashCommitment")
        expected_link_hash = hashlib.sha256(f"{right_id}:{mb_id_hash}".encode()).hexdigest()
        
        if expected_link_hash != proof.get("linkHash"):
            logging.error("Link hash verification failed")
            return False
        
        # All verifications passed
        logging.info("✓ Proof successfully verified")
        return True
    
    def verify_proof_file(self, proof_file):
        """Verify proofs from a file"""
        try:
            # Load proofs from file
            with open(proof_file, 'r') as f:
                proofs = json.load(f)
            
            if not isinstance(proofs, list):
                proofs = [proofs]
            
            results = []
            for i, proof_data in enumerate(proofs):
                logging.info(f"Verifying proof {i+1}/{len(proofs)}")
                
                # Display work info if available
                if "work_info" in proof_data:
                    work_info = proof_data["work_info"]
                    logging.info(f"Work: {work_info.get('title')} by {work_info.get('artist')}")
                
                # Verify the proof
                is_valid = self.verify_proof(proof_data)
                
                # Store result
                results.append({
                    "proof_index": i,
                    "right_id": proof_data.get("proof", {}).get("rightId"),
                    "verified": is_valid
                })
            
            # Print summary
            logging.info(f"Verified {len(proofs)} proofs")
            logging.info(f"Successfully verified: {sum(1 for r in results if r['verified'])}")
            logging.info(f"Failed verification: {sum(1 for r in results if not r['verified'])}")
            
            return results
            
        except Exception as e:
            logging.error(f"Error verifying proofs: {e}")
            return []
    
    def simulate_selective_reveal(self, proof_data):
        """
        Simulate selective disclosure of proof data
        This demonstrates how a user could reveal specific info to third parties
        """
        # Extract the proof
        proof = proof_data.get("proof", {})
        work_info = proof_data.get("work_info", {})
        
        # Create different disclosure levels
        minimal_disclosure = {
            "rightId": proof.get("rightId"),
            "proofType": proof.get("proofType"),
            "verified": True,
            "timestamp": proof.get("timestamp")
        }
        
        standard_disclosure = {
            **minimal_disclosure,
            "workTitle": work_info.get("title"),
            "mbIdHash": proof.get("mbIdHashCommitment")
        }
        
        full_disclosure = {
            **standard_disclosure,
            "artistName": work_info.get("artist"),
            "mbId": work_info.get("mb_id")
        }
        
        return {
            "minimal": minimal_disclosure,
            "standard": standard_disclosure,
            "full": full_disclosure
        }

def print_proof_details(proof_data):
    """Print details of a proof in a readable format"""
    proof = proof_data.get("proof", {})
    work_info = proof_data.get("work_info", {})
    
    print("\n" + "="*60)
    print("ZERO-KNOWLEDGE PROOF DETAILS")
    print("="*60)
    
    if work_info:
        print(f"\nWork Information:")
        print(f"  Title: {work_info.get('title')}")
        print(f"  Artist: {work_info.get('artist')}")
        print(f"  MusicBrainz ID: {work_info.get('mb_id')}")
    
    print(f"\nProof Data:")
    print(f"  Right ID: {proof.get('rightId')}")
    print(f"  Proof Type: {proof.get('proofType')}")
    print(f"  MusicBrainz ID Hash: {proof.get('mbIdHashCommitment')}")
    print(f"  Link Hash: {proof.get('linkHash')}")
    print(f"  Salt: {proof.get('salt')}")
    print(f"  Timestamp: {proof.get('timestamp')}")
    
    print(f"\nSignature: {proof_data.get('signature')}")
    
    if "explanation" in proof_data:
        explanation = proof_data.get("explanation", {})
        print(f"\nPurpose:")
        print(f"  {explanation.get('purpose')}")
        
        print(f"\nVerification Process:")
        for step in explanation.get("verification_process", []):
            print(f"  {step}")
        
        print(f"\nPrivacy Benefits:")
        for benefit in explanation.get("privacy_benefits", []):
            print(f"  - {benefit}")
    
    print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(description="Verify zero-knowledge proofs")
    parser.add_argument("--proofs", default="detailed_zk_proofs.json", help="Path to proof file")
    parser.add_argument("--reveal", action="store_true", help="Show selective disclosure examples")
    args = parser.parse_args()
    
    verifier = ProofVerifier()
    
    # Verify proofs
    results = verifier.verify_proof_file(args.proofs)
    
    # Load proofs for display
    with open(args.proofs, 'r') as f:
        proofs = json.load(f)
    
    if not isinstance(proofs, list):
        proofs = [proofs]
    
    # Display detailed proof information
    for proof_data in proofs:
        print_proof_details(proof_data)
        
        # Show selective disclosure examples if requested
        if args.reveal:
            disclosures = verifier.simulate_selective_reveal(proof_data)
            
            print("\nSelective Disclosure Examples:")
            print("\nMinimal Disclosure (Just the rights confirmation):")
            print(json.dumps(disclosures["minimal"], indent=2))
            
            print("\nStandard Disclosure (Rights and work title):")
            print(json.dumps(disclosures["standard"], indent=2))
            
            print("\nFull Disclosure (All information):")
            print(json.dumps(disclosures["full"], indent=2))

if __name__ == "__main__":
    main() 