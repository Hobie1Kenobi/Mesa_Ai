import os
import json
import logging
import hashlib
import time
import base64
import tempfile
from pathlib import Path
from web3 import Web3
from privacy_layer import PrivacyLayer
from key_management import KeyVault

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mesa_vault_demo.log')
    ]
)

# Sample rights data
SAMPLE_RIGHTS = [
    {
        "work_title": "Midnight Dreams",
        "artist_party": "Sarah Wilson",
        "publisher_party": "Dreamlight Records",
        "rights_type": "Publishing",
        "territory": "Global",
        "term": "2 years with renewal option",
        "royalty_info": [
            {"party": "Sarah Wilson", "percentage": 0.5},
            {"party": "Dreamlight Records", "percentage": 0.5}
        ],
        "effective_date": "2025-04-01"
    },
    {
        "work_title": "Electronic Horizon",
        "artist_party": "The Lunar Echoes",
        "publisher_party": "Skyline Arena Entertainment LLC",
        "rights_type": "Performance",
        "territory": "Las Vegas, Nevada",
        "term": "3 months",
        "royalty_info": [
            {"party": "The Lunar Echoes", "percentage": 0.75},
            {"party": "Skyline Arena Entertainment LLC", "percentage": 0.25}
        ],
        "effective_date": "2025-05-15"
    },
    {
        "work_title": "Harmony Collection",
        "artist_party": "Daniel Morgan",
        "publisher_party": "Harmonic Bridge Publishing Group",
        "rights_type": "Publishing",
        "territory": "Global",
        "term": "3 years with renewal options",
        "royalty_info": [
            {"party": "Daniel Morgan", "percentage": 0.5},
            {"party": "Harmonic Bridge Publishing Group", "percentage": 0.5}
        ],
        "effective_date": "2025-03-18"
    }
]

# Sample collaborators
COLLABORATORS = [
    {
        "name": "Streaming Platform",
        "required_fields": ["work_title", "rights_type", "territory", "effective_date"]
    },
    {
        "name": "Royalty Collection Agency",
        "required_fields": ["work_title", "artist_party", "publisher_party", "royalty_info"]
    },
    {
        "name": "Performance Venue",
        "required_fields": ["work_title", "artist_party", "territory", "effective_date", "term"]
    }
]

# Blockchain configuration
BLOCKCHAIN_NETWORK = "Base Sepolia"
WALLET_ADDRESS = "0x7338af1E9d6dbc4cc1Efa067C0775Bf222aDb0C3"
CONTRACT_ADDRESS = "0x7338af1E9d6dbc4cc1Efa067C0775Bf222aDb0C3"

class MESARightsVault:
    """
    MESA Rights Vault - A comprehensive system for privacy-preserving music rights
    management with blockchain integration and secure key management.
    """
    
    def __init__(self):
        """Initialize the MESA Rights Vault system"""
        # Create a temporary directory for the demo
        self.temp_dir = tempfile.mkdtemp()
        logging.info(f"Using temporary storage at: {self.temp_dir}")
        
        # Initialize key vault
        self.key_vault = KeyVault(storage_dir=self.temp_dir)
        logging.info("Key vault initialized")
        
        # Initialize privacy layer
        self.privacy_layer = PrivacyLayer()
        logging.info("Privacy layer initialized")
        
        # State
        self.rights_registry = {}
        self.user_profile = None
        self.blockchain_connected = False
    
    def setup_user_account(self, username, password):
        """
        Set up a new user account
        
        Args:
            username (str): User's name
            password (str): Strong password
            
        Returns:
            dict: User profile information
        """
        # Create vault for the user
        vault_info = self.key_vault.create_new_vault(password)
        
        # Connect wallet
        self.key_vault.connect_wallet(WALLET_ADDRESS, wallet_type="coinbase")
        
        # Create user profile
        self.user_profile = {
            "username": username,
            "vault_id": vault_info["vault_id"],
            "recovery_phrase": vault_info["recovery_phrase"],
            "created_at": vault_info["created_at"],
            "wallet_address": WALLET_ADDRESS
        }
        
        logging.info(f"User account created: {username} (Vault ID: {vault_info['vault_id']})")
        return self.user_profile
    
    def register_rights(self, rights_data):
        """
        Register new music rights with privacy protection
        
        Args:
            rights_data (dict): Rights information
            
        Returns:
            dict: Rights registration information
        """
        # Generate a unique rights ID
        timestamp = int(time.time())
        rights_id = hashlib.sha256(f"{rights_data['work_title']}:{timestamp}".encode()).hexdigest()[:16]
        
        # Create encryption key for this rights entry
        encryption_key_b64 = self.key_vault.create_rights_key(rights_id, {
            "title": rights_data["work_title"],
            "artist": rights_data["artist_party"],
            "created_at": timestamp
        })
        
        # Convert from base64 to bytes for the privacy layer
        encryption_key = base64.b64decode(encryption_key_b64)
        
        # Set the encryption key in the privacy layer
        self.privacy_layer.master_key = encryption_key
        
        # Encrypt the rights data
        encrypted_package = self.privacy_layer.encrypt_rights_data(rights_data)
        
        # Prepare for blockchain
        right_id_bytes32 = "0x" + rights_id.ljust(64, '0')
        blockchain_params = {
            "rightId": right_id_bytes32,
            "encryptedData": "0x" + encrypted_package["encrypted_data"],
            "metadataHash": "0x" + encrypted_package["metadata_hash"],
            "display": {
                "workTitle": rights_data["work_title"],
                "rightsHolder": rights_data["publisher_party"],
                "rightsType": rights_data["rights_type"],
                "territory": rights_data["territory"]
            }
        }
        
        # Store in registry
        self.rights_registry[rights_id] = {
            "rights_id": rights_id,
            "blockchain_params": blockchain_params,
            "metadata": {
                "work_title": rights_data["work_title"],
                "artist": rights_data["artist_party"],
                "publisher": rights_data["publisher_party"],
                "registered_at": timestamp
            },
            "original_data": rights_data
        }
        
        # Simulate blockchain registration
        tx_hash = f"0x{''.join(['0123456789abcdef'[i % 16] for i in range(64)])}"
        block_number = 12345678
        
        registration_info = {
            "rights_id": rights_id,
            "blockchain": {
                "network": BLOCKCHAIN_NETWORK,
                "tx_hash": tx_hash,
                "block_number": block_number,
                "contract_address": CONTRACT_ADDRESS
            },
            "metadata": self.rights_registry[rights_id]["metadata"]
        }
        
        logging.info(f"Rights registered: {rights_data['work_title']} (ID: {rights_id})")
        return registration_info
    
    def create_sharing_profile(self, rights_id, recipient_name, fields_to_share):
        """
        Create a selective disclosure profile for sharing rights
        
        Args:
            rights_id (str): Rights identifier
            recipient_name (str): Name of the recipient
            fields_to_share (list): Fields to include in the disclosure
            
        Returns:
            dict: Sharing profile information
        """
        if rights_id not in self.rights_registry:
            logging.error(f"Rights ID not found: {rights_id}")
            return None
        
        # Get the original rights data
        rights_data = self.rights_registry[rights_id]["original_data"]
        
        # Get the encryption key from the key vault
        encryption_key_b64 = self.key_vault.get_rights_key(rights_id)
        encryption_key = base64.b64decode(encryption_key_b64)
        
        # Set the key in the privacy layer
        self.privacy_layer.master_key = encryption_key
        
        # Create selective disclosure proof
        disclosure = self.privacy_layer.create_disclosure_proof(
            rights_data,
            fields_to_disclose=fields_to_share
        )
        
        # Create the sharing profile
        profile_id = hashlib.sha256(f"{rights_id}:{recipient_name}:{time.time()}".encode()).hexdigest()[:16]
        
        sharing_profile = {
            "profile_id": profile_id,
            "rights_id": rights_id,
            "recipient": recipient_name,
            "created_at": int(time.time()),
            "disclosed_fields": fields_to_share,
            "disclosure_proof": disclosure
        }
        
        # Store in the registry
        if "sharing_profiles" not in self.rights_registry[rights_id]:
            self.rights_registry[rights_id]["sharing_profiles"] = {}
        
        self.rights_registry[rights_id]["sharing_profiles"][profile_id] = sharing_profile
        
        logging.info(f"Sharing profile created for {recipient_name} (ID: {profile_id})")
        return sharing_profile
    
    def verify_disclosure(self, profile_id, rights_id):
        """
        Verify a selective disclosure proof
        
        Args:
            profile_id (str): Sharing profile identifier
            rights_id (str): Rights identifier
            
        Returns:
            dict: Verification result
        """
        if rights_id not in self.rights_registry:
            logging.error(f"Rights ID not found: {rights_id}")
            return {"valid": False, "error": "Rights ID not found"}
        
        if "sharing_profiles" not in self.rights_registry[rights_id]:
            return {"valid": False, "error": "No sharing profiles found"}
        
        if profile_id not in self.rights_registry[rights_id]["sharing_profiles"]:
            return {"valid": False, "error": "Profile ID not found"}
        
        # Get the sharing profile
        profile = self.rights_registry[rights_id]["sharing_profiles"][profile_id]
        
        # Get the encryption key from the key vault
        encryption_key_b64 = self.key_vault.get_rights_key(rights_id)
        encryption_key = base64.b64decode(encryption_key_b64)
        
        # Set the key in the privacy layer
        self.privacy_layer.master_key = encryption_key
        
        # Get the metadata hash from the blockchain parameters
        metadata_hash = self.rights_registry[rights_id]["blockchain_params"]["metadataHash"][2:]  # Remove '0x'
        
        # Verify the disclosure
        is_valid = self.privacy_layer.verify_disclosure_proof(profile["disclosure_proof"], metadata_hash)
        
        verification_result = {
            "valid": is_valid,
            "rights_id": rights_id,
            "profile_id": profile_id,
            "recipient": profile["recipient"],
            "disclosed_fields": profile["disclosed_fields"],
            "verified_at": int(time.time())
        }
        
        if is_valid:
            verification_result["disclosed_data"] = profile["disclosure_proof"]["disclosed_data"]
        
        logging.info(f"Disclosure verification: {is_valid} (Profile ID: {profile_id})")
        return verification_result
    
    def create_ownership_proof(self, rights_id):
        """
        Create a zero-knowledge proof of ownership
        
        Args:
            rights_id (str): Rights identifier
            
        Returns:
            dict: Ownership proof
        """
        if rights_id not in self.rights_registry:
            logging.error(f"Rights ID not found: {rights_id}")
            return None
        
        # Get the original rights data
        rights_data = self.rights_registry[rights_id]["original_data"]
        
        # Get the encryption key from the key vault
        encryption_key_b64 = self.key_vault.get_rights_key(rights_id)
        encryption_key = base64.b64decode(encryption_key_b64)
        
        # Set the key in the privacy layer
        self.privacy_layer.master_key = encryption_key
        
        # Create ownership proof
        ownership_proof = self.privacy_layer.create_ownership_proof(
            rights_data,
            WALLET_ADDRESS
        )
        
        logging.info(f"Ownership proof created for {rights_id}")
        return ownership_proof
    
    def verify_ownership(self, ownership_proof):
        """
        Verify a zero-knowledge proof of ownership
        
        Args:
            ownership_proof (dict): Ownership proof
            
        Returns:
            dict: Verification result
        """
        # Get the rights ID from the work ID in the proof
        work_id = ownership_proof["work_id"]
        rights_id = None
        
        # Find the matching rights entry
        for rid, rights_info in self.rights_registry.items():
            # Compute the work ID from the work title
            rights_data = rights_info["original_data"]
            computed_work_id = hashlib.sha256(str(rights_data.get("work_title", "")).encode()).hexdigest()[:16]
            
            if computed_work_id == work_id:
                rights_id = rid
                break
        
        if not rights_id:
            return {"valid": False, "error": "Work ID not found in registry"}
        
        # Get the encryption key from the key vault
        encryption_key_b64 = self.key_vault.get_rights_key(rights_id)
        encryption_key = base64.b64decode(encryption_key_b64)
        
        # Set the key in the privacy layer
        self.privacy_layer.master_key = encryption_key
        
        # Verify the ownership proof
        is_valid = self.privacy_layer.verify_ownership_proof(ownership_proof, WALLET_ADDRESS)
        
        verification_result = {
            "valid": is_valid,
            "rights_id": rights_id,
            "work_id": work_id,
            "claimed_owner": WALLET_ADDRESS,
            "verified_at": int(time.time())
        }
        
        if is_valid:
            verification_result["work_title"] = self.rights_registry[rights_id]["metadata"]["work_title"]
        
        logging.info(f"Ownership verification: {is_valid} (Rights ID: {rights_id})")
        return verification_result
    
    def create_royalty_verification(self, rights_id, payment_amount):
        """
        Create a royalty payment verification proof
        
        Args:
            rights_id (str): Rights identifier
            payment_amount (float): Amount being paid
            
        Returns:
            dict: Royalty verification proof
        """
        if rights_id not in self.rights_registry:
            logging.error(f"Rights ID not found: {rights_id}")
            return None
        
        # Get the original rights data
        rights_data = self.rights_registry[rights_id]["original_data"]
        
        # Get the encryption key from the key vault
        encryption_key_b64 = self.key_vault.get_rights_key(rights_id)
        encryption_key = base64.b64decode(encryption_key_b64)
        
        # Set the key in the privacy layer
        self.privacy_layer.master_key = encryption_key
        
        # Create royalty verification
        royalty_proof = self.privacy_layer.create_royalty_verification(
            rights_data,
            payment_amount
        )
        
        logging.info(f"Royalty verification created for {rights_id} (Amount: ${payment_amount})")
        return royalty_proof
    
    def backup_user_data(self):
        """
        Create a secure backup of all user data
        
        Returns:
            dict: Backup information
        """
        # Create vault backup
        backup_info = self.key_vault.backup_vault()
        
        # Add rights registry to the backup info
        backup_registry_path = Path(self.temp_dir) / "rights_registry_backup.json"
        with open(backup_registry_path, 'w') as f:
            json.dump(self.rights_registry, f)
        
        backup_info["rights_registry_path"] = str(backup_registry_path)
        backup_info["rights_count"] = len(self.rights_registry)
        
        logging.info(f"User data backed up: {backup_info['backup_id']}")
        return backup_info

def run_mesa_demo():
    """Run a comprehensive demo of the MESA Rights Vault system"""
    print("\n============================================================")
    print("=== MESA RIGHTS VAULT: PRIVACY-FIRST MUSIC RIGHTS DEMO ===")
    print("============================================================\n")
    
    # Initialize the MESA Rights Vault
    mesa = MESARightsVault()
    
    # Step 1: User Setup
    print("STEP 1: ARTIST ACCOUNT SETUP\n")
    user_profile = mesa.setup_user_account("Sarah Wilson", "MySecurePassword123!")
    
    print(f"Artist: {user_profile['username']}")
    print(f"Vault ID: {user_profile['vault_id']}")
    print(f"Recovery Phrase: {user_profile['recovery_phrase']}")
    print(f"Wallet Address: {user_profile['wallet_address']}")
    print(f"Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(user_profile['created_at']))}")
    
    # Step 2: Rights Registration
    print("\n\nSTEP 2: REGISTERING RIGHTS ON BLOCKCHAIN\n")
    rights_registrations = []
    
    for idx, rights_data in enumerate(SAMPLE_RIGHTS):
        print(f"Registering Work {idx+1}: {rights_data['work_title']}")
        registration = mesa.register_rights(rights_data)
        rights_registrations.append(registration)
        
        print(f"  Rights ID: {registration['rights_id']}")
        print(f"  Blockchain: {registration['blockchain']['network']}")
        print(f"  Transaction: {registration['blockchain']['tx_hash'][:10]}...")
        print(f"  Block: {registration['blockchain']['block_number']}")
        print(f"  Artist: {registration['metadata']['artist']}")
        print(f"  Publisher: {registration['metadata']['publisher']}")
        print()
    
    # Step 3: Selective Disclosure
    print("\nSTEP 3: SELECTIVE DISCLOSURE FOR DIFFERENT PLATFORMS\n")
    
    sharing_profiles = []
    verification_results = []
    
    for idx, collaborator in enumerate(COLLABORATORS):
        # Use a different rights entry for each collaborator
        rights_idx = idx % len(rights_registrations)
        rights_id = rights_registrations[rights_idx]['rights_id']
        rights_title = rights_registrations[rights_idx]['metadata']['work_title']
        
        print(f"Creating Sharing Profile for: {collaborator['name']}")
        print(f"  Work: {rights_title}")
        print(f"  Sharing Fields: {', '.join(collaborator['required_fields'])}")
        
        # Create sharing profile
        profile = mesa.create_sharing_profile(
            rights_id,
            collaborator['name'],
            collaborator['required_fields']
        )
        sharing_profiles.append(profile)
        
        # Verify the disclosure
        verification = mesa.verify_disclosure(profile['profile_id'], rights_id)
        verification_results.append(verification)
        
        print(f"  Profile ID: {profile['profile_id']}")
        print(f"  Verification: {'✓ Valid' if verification['valid'] else '✗ Invalid'}")
        
        if verification['valid'] and 'disclosed_data' in verification:
            print("  Shared Data:")
            for field, value in verification['disclosed_data'].items():
                print(f"    - {field}: {value if not isinstance(value, list) else '(complex data)'}")
        print()
    
    # Step 4: Ownership Proofs
    print("\nSTEP 4: ZERO-KNOWLEDGE OWNERSHIP PROOFS\n")
    
    # Create ownership proof for the first rights entry
    rights_id = rights_registrations[0]['rights_id']
    work_title = rights_registrations[0]['metadata']['work_title']
    
    print(f"Creating Zero-Knowledge Ownership Proof for '{work_title}'")
    ownership_proof = mesa.create_ownership_proof(rights_id)
    
    print(f"  Work ID: {ownership_proof['work_id']}")
    print(f"  Rights Type: {ownership_proof['rights_type']}")
    print(f"  Proof Type: {ownership_proof['proof_type']}")
    
    # Verify ownership
    ownership_verification = mesa.verify_ownership(ownership_proof)
    
    print(f"  Verification: {'✓ Valid' if ownership_verification['valid'] else '✗ Invalid'}")
    if ownership_verification['valid']:
        print(f"  Confirmed Work: {ownership_verification['work_title']}")
    print()
    
    # Step 5: Royalty Verification
    print("\nSTEP 5: PRIVACY-PRESERVING ROYALTY VERIFICATION\n")
    
    # Create royalty verification for the second rights entry
    rights_id = rights_registrations[1]['rights_id']
    work_title = rights_registrations[1]['metadata']['work_title']
    payment_amount = 10000.00
    
    print(f"Creating Royalty Verification for '{work_title}'")
    print(f"Payment Amount: ${payment_amount}")
    
    royalty_proof = mesa.create_royalty_verification(rights_id, payment_amount)
    
    print("Expected Payments (Without Revealing Percentages):")
    for party, amount in royalty_proof['expected_payments'].items():
        print(f"  - {party}: ${amount}")
    
    # Step 6: Secure Backup
    print("\n\nSTEP 6: SECURE DATA BACKUP\n")
    
    backup_info = mesa.backup_user_data()
    
    print(f"Created Encrypted Backup of All Rights Data")
    print(f"  Backup ID: {backup_info['backup_id']}")
    print(f"  Rights Entries: {backup_info['rights_count']}")
    print(f"  Protection: {backup_info['protected_with']}")
    print(f"  Size: {backup_info['size_bytes']} bytes")
    print(f"  Path: {backup_info['path']}")
    
    # Summary
    print("\n\n=== MESA RIGHTS VAULT DEMONSTRATION SUMMARY ===\n")
    print(f"User: {user_profile['username']}")
    print(f"Rights Registered: {len(rights_registrations)}")
    print(f"Sharing Profiles Created: {len(sharing_profiles)}")
    print(f"Privacy Features Demonstrated:")
    print("  1. End-to-end encryption for blockchain storage")
    print("  2. Selective disclosure for different platforms")
    print("  3. Zero-knowledge ownership proofs")
    print("  4. Privacy-preserving royalty verification")
    print("  5. Secure key management with recovery")
    print("  6. Smart wallet integration")
    print("\nThis system enables artists to maintain control over their rights")
    print("data while securely sharing it with partners and verifying ownership")
    print("without revealing sensitive contract details.")
    print("\n============================================================")

if __name__ == "__main__":
    run_mesa_demo() 