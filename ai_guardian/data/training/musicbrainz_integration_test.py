#!/usr/bin/env python3

import os
import json
import hashlib
import time
import argparse
import logging
from pathlib import Path
import requests
from cryptography.fernet import Fernet

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('musicbrainz_integration.log')
    ]
)

class MusicBrainzIntegrationTester:
    """
    Tester for MusicBrainz integration with MESA Rights Vault
    """
    
    def __init__(self, config_dir=None):
        """Initialize the integration tester"""
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path('.')
        
        # Load schemas
        self.load_schemas()
        
        # Generate encryption key for privacy layer
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Set up MusicBrainz API parameters
        self.mb_api_base = "https://musicbrainz.org/ws/2"
        self.mb_user_agent = {
            "User-Agent": "MESA_Rights_Vault_Test/0.1 (https://example.com/mesa)"
        }
    
    def load_schemas(self):
        """Load MusicBrainz and rights schemas"""
        try:
            # Load MusicBrainz schema
            with open(self.config_dir / 'musicbrainz_schema.json', 'r') as f:
                self.mb_schema = json.load(f)
            logging.info("Loaded MusicBrainz schema")
            
            # Load music rights schema
            with open(self.config_dir / 'music_rights_schema.json', 'r') as f:
                self.rights_schema = json.load(f)
            logging.info("Loaded music rights schema")
            
            # Load sample rights data for testing
            with open(self.config_dir / 'sample_music_rights.json', 'r') as f:
                self.sample_rights = json.load(f)
            logging.info(f"Loaded {len(self.sample_rights.get('rights', []))} sample rights")
            
        except Exception as e:
            logging.error(f"Error loading schemas: {e}")
            raise
    
    def test_musicbrainz_api(self, limit=3):
        """Test basic access to MusicBrainz API"""
        logging.info("Testing MusicBrainz API access")
        
        # Test searching for works
        test_works = [
            "Bohemian Rhapsody",
            "Yesterday",
            "Imagine"
        ]
        
        results = []
        for work in test_works[:limit]:
            try:
                url = f"{self.mb_api_base}/work/?query=work:{work}&fmt=json"
                response = requests.get(url, headers=self.mb_user_agent)
                
                if response.status_code == 200:
                    data = response.json()
                    count = data.get('count', 0)
                    logging.info(f"Found {count} results for '{work}'")
                    
                    # Add to results
                    if count > 0 and 'works' in data:
                        work_data = {
                            'query': work,
                            'count': count,
                            'sample_result': data['works'][0] if data['works'] else None
                        }
                        results.append(work_data)
                else:
                    logging.warning(f"Failed to search for '{work}'. Status code: {response.status_code}")
                
                # Be nice to the API - don't hammer it
                time.sleep(1)
            
            except Exception as e:
                logging.error(f"Error searching for work '{work}': {e}")
        
        return results
    
    def map_fields(self, mb_entity, entity_type="Work"):
        """Map MusicBrainz entity fields to MESA Rights schema"""
        if entity_type == "Work":
            # Map Work fields to our schema
            mapped_data = {
                "workTitle": mb_entity.get("title", "Unknown Work"),
                "identifiers": {}
            }
            
            # Add ISWC if available
            if "iswcs" in mb_entity and mb_entity["iswcs"]:
                mapped_data["identifiers"]["iswc"] = mb_entity["iswcs"][0]
            
            # Add composer information if available
            if "artist-relation-list" in mb_entity:
                composers = [rel["artist"]["name"] for rel in mb_entity["artist-relation-list"] 
                            if rel.get("type") == "composer"]
                if composers:
                    mapped_data["artistParty"] = composers[0]
            
            return mapped_data
        
        elif entity_type == "Recording":
            # Map Recording fields to our schema
            mapped_data = {
                "workTitle": mb_entity.get("title", "Unknown Recording"),
                "identifiers": {}
            }
            
            # Add ISRC if available
            if "isrcs" in mb_entity and mb_entity["isrcs"]:
                mapped_data["identifiers"]["isrc"] = mb_entity["isrcs"][0]
            
            # Add artist information
            if "artist-credit" in mb_entity:
                artists = [credit["artist"]["name"] for credit in mb_entity["artist-credit"]]
                if artists:
                    mapped_data["artistParty"] = artists[0]
            
            return mapped_data
        
        else:
            logging.warning(f"Unsupported entity type: {entity_type}")
            return {}
    
    def test_privacy_layer(self, mb_entity, entity_type="Work"):
        """Test privacy-preserving storage and selective disclosure"""
        logging.info(f"Testing privacy layer with {entity_type}")
        
        # Map MB entity to our schema
        mapped_data = self.map_fields(mb_entity, entity_type)
        
        # Add necessary fields to make it a valid Rights entity
        mapped_data["rightId"] = f"0x{hashlib.sha256(json.dumps(mb_entity).encode()).hexdigest()[:40]}"
        mapped_data["rightsType"] = "Publishing" if entity_type == "Work" else "Master"
        mapped_data["territory"] = "Global"
        mapped_data["effectiveDate"] = "2025-01-01"
        
        # 1. Test encrypted storage
        encrypted_data = self.encrypt_entity(mapped_data)
        logging.info(f"Successfully encrypted {entity_type} data")
        
        # 2. Test selective disclosure
        public_fields = ["workTitle", "rightsType", "territory"]
        private_fields = ["rightId", "identifiers", "effectiveDate"]
        
        # Create selectively disclosed version
        disclosed_data = {field: mapped_data[field] for field in public_fields if field in mapped_data}
        
        # Create link record with privacy controls
        record = {
            "mb_id": mb_entity.get("id", "unknown"),
            "mb_id_hash": hashlib.sha256(mb_entity.get("id", "unknown").encode()).hexdigest(),
            "encrypted_data": encrypted_data,
            "public_fields": disclosed_data,
            "has_private_data": len(private_fields) > 0,
            "created_at": int(time.time())
        }
        
        # Verify we can decrypt the full data
        decrypted = self.decrypt_entity(encrypted_data)
        fields_match = all(decrypted.get(field) == mapped_data.get(field) for field in mapped_data)
        
        if fields_match:
            logging.info("Successfully verified data encryption/decryption")
        else:
            logging.error("Data mismatch after decryption!")
        
        return {
            "record": record,
            "verification": fields_match
        }
    
    def test_with_sample_data(self):
        """Test integration using our sample data"""
        logging.info("Testing integration with sample rights data")
        
        results = []
        sample_rights = self.sample_rights.get('rights', [])[:3]  # Test with first 3 samples
        
        for right in sample_rights:
            # 1. Try to find a matching work in MusicBrainz
            work_title = right.get('workTitle', '')
            artist = right.get('artistParty', '')
            
            try:
                query = f"work:{work_title}"
                if artist:
                    query += f" AND artist:{artist}"
                
                url = f"{self.mb_api_base}/work/?query={query}&fmt=json"
                response = requests.get(url, headers=self.mb_user_agent)
                
                if response.status_code == 200:
                    data = response.json()
                    count = data.get('count', 0)
                    
                    if count > 0 and 'works' in data:
                        mb_work = data['works'][0]
                        match_score = self.calculate_match_score(right, mb_work)
                        
                        # Test privacy layer with this match
                        privacy_result = self.test_privacy_layer(mb_work, "Work")
                        
                        result = {
                            'right_id': right.get('rightId'),
                            'title': work_title,
                            'artist': artist,
                            'mb_match': mb_work.get('id'),
                            'match_score': match_score,
                            'privacy_test': privacy_result.get('verification')
                        }
                        results.append(result)
                        
                        logging.info(f"Tested '{work_title}' with match score: {match_score}")
                    else:
                        logging.info(f"No matches found for '{work_title}'")
                        results.append({
                            'right_id': right.get('rightId'),
                            'title': work_title,
                            'artist': artist,
                            'mb_match': None,
                            'match_score': 0,
                            'privacy_test': False
                        })
                else:
                    logging.warning(f"API error for '{work_title}'. Status: {response.status_code}")
                
                # Be nice to the API
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Error testing with '{work_title}': {e}")
        
        return results
    
    def calculate_match_score(self, right, mb_entity):
        """Calculate a match score between a right and MB entity"""
        score = 0
        
        # Compare title
        right_title = right.get('workTitle', '').lower()
        mb_title = mb_entity.get('title', '').lower()
        
        if right_title == mb_title:
            score += 50
        elif right_title in mb_title or mb_title in right_title:
            score += 30
        
        # Compare artist
        right_artist = right.get('artistParty', '').lower()
        mb_artists = []
        
        if "artist-relation-list" in mb_entity:
            mb_artists = [rel["artist"]["name"].lower() for rel in mb_entity["artist-relation-list"]]
        
        if right_artist in mb_artists:
            score += 50
        elif any(right_artist in artist or artist in right_artist for artist in mb_artists):
            score += 30
        
        # Compare identifiers
        right_iswc = right.get('identifiers', {}).get('iswc', '')
        mb_iswcs = mb_entity.get('iswcs', [])
        
        if right_iswc and right_iswc in mb_iswcs:
            score += 100
        
        return min(score, 100)  # Cap at 100
    
    def encrypt_entity(self, entity_data):
        """Encrypt an entity for privacy-preserving storage"""
        data_json = json.dumps(entity_data)
        encrypted_data = self.cipher.encrypt(data_json.encode())
        return encrypted_data.decode()
    
    def decrypt_entity(self, encrypted_data):
        """Decrypt an entity from privacy-preserving storage"""
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data.encode())
            return json.loads(decrypted_data)
        except Exception as e:
            logging.error(f"Failed to decrypt data: {e}")
            return {}
    
    def create_zk_proof_simulation(self, right_id, mb_id_hash):
        """Simulate creating a zero-knowledge proof linking right to MB"""
        # This is a simulation of what would be done with a real ZK proof system
        
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
        
        return {
            "proof": proof,
            "signature": signature,
            "verified": True
        }
    
    def run_full_test(self):
        """Run a full integration test"""
        logging.info("Starting full MusicBrainz integration test")
        
        # 1. Test basic API access
        api_results = self.test_musicbrainz_api()
        
        # 2. Test with our sample data
        sample_results = self.test_with_sample_data()
        
        # 3. If we have API results, test ZK proof simulation
        zk_results = []
        if api_results and sample_results:
            for i, sample in enumerate(sample_results):
                if sample.get('mb_match'):
                    right_id = sample.get('right_id')
                    mb_id = sample.get('mb_match')
                    mb_id_hash = hashlib.sha256(mb_id.encode()).hexdigest()
                    
                    zk_proof = self.create_zk_proof_simulation(right_id, mb_id_hash)
                    zk_results.append({
                        'right_id': right_id,
                        'mb_id': mb_id,
                        'proof_generated': True,
                        'verification': zk_proof.get('verified', False)
                    })
                    
                    logging.info(f"Generated ZK proof simulation for {right_id}")
        
        # Combine results
        full_results = {
            'api_test': len(api_results) > 0,
            'sample_matches': [r for r in sample_results if r.get('mb_match')],
            'zk_proofs': zk_results,
            'timestamp': int(time.time())
        }
        
        # Save results
        with open('integration_test_results.json', 'w') as f:
            json.dump(full_results, f, indent=2)
        
        logging.info("Integration test completed")
        return full_results

def main():
    """Main function to run the integration tests"""
    parser = argparse.ArgumentParser(description="Test MusicBrainz integration")
    parser.add_argument("--config", default=".", help="Path to config directory")
    args = parser.parse_args()
    
    tester = MusicBrainzIntegrationTester(args.config)
    results = tester.run_full_test()
    
    print(f"Test completed. Found {len(results['sample_matches'])} matches and generated {len(results['zk_proofs'])} ZK proofs.")

if __name__ == "__main__":
    main() 