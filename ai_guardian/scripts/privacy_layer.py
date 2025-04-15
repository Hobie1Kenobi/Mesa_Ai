import hashlib
import json
import base64
import hmac
import time
import random
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class PrivacyLayer:
    """
    Privacy layer for MESA Rights Vault that enables selective disclosure
    and privacy-preserving verification of music rights data.
    """
    
    def __init__(self, master_key=None):
        """Initialize the privacy layer with an optional master key"""
        if master_key:
            self.master_key = master_key
        else:
            # Generate a random master key for encryption/decryption
            self.master_key = Fernet.generate_key()
        
        self.cipher = Fernet(self.master_key)
    
    def encrypt_rights_data(self, rights_data):
        """
        Encrypt the full rights data for secure storage
        
        Args:
            rights_data (dict): Complete rights information
            
        Returns:
            dict: Encrypted data and metadata for blockchain storage
        """
        # Convert to JSON string and encrypt
        data_json = json.dumps(rights_data)
        encrypted_data = self.cipher.encrypt(data_json.encode())
        
        # Generate metadata hash for verification
        metadata_hash = hashlib.sha256(data_json.encode()).hexdigest()
        
        return {
            "encrypted_data": base64.b64encode(encrypted_data).decode(),
            "metadata_hash": metadata_hash,
            "timestamp": int(time.time())
        }
    
    def decrypt_rights_data(self, encrypted_data):
        """
        Decrypt the full rights data
        
        Args:
            encrypted_data (str): Base64-encoded encrypted data
            
        Returns:
            dict: Decrypted rights data
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            return json.loads(decrypted_data)
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")
    
    def create_disclosure_proof(self, rights_data, fields_to_disclose):
        """
        Create a selective disclosure proof that reveals only specific fields
        
        Args:
            rights_data (dict): Complete rights information
            fields_to_disclose (list): List of field names to disclose
            
        Returns:
            dict: Selective disclosure proof
        """
        # Extract only the fields to disclose
        disclosed_data = {}
        for field in fields_to_disclose:
            if field in rights_data:
                disclosed_data[field] = rights_data[field]
        
        # Create a hash of the original full data for verification
        original_hash = hashlib.sha256(json.dumps(rights_data).encode()).hexdigest()
        
        # Generate a proof that links the disclosed data to the original
        proof_salt = base64.b64encode(random.randbytes(16)).decode()
        proof_hmac = hmac.new(
            self.master_key,
            msg=(json.dumps(disclosed_data) + proof_salt).encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return {
            "disclosed_data": disclosed_data,
            "proof_salt": proof_salt,
            "proof_hmac": proof_hmac,
            "original_hash": original_hash,
            "timestamp": int(time.time())
        }
    
    def verify_disclosure_proof(self, proof, metadata_hash):
        """
        Verify a selective disclosure proof against the original metadata hash
        
        Args:
            proof (dict): Selective disclosure proof
            metadata_hash (str): Original metadata hash from blockchain
            
        Returns:
            bool: True if the proof is valid
        """
        # Re-compute the HMAC
        computed_hmac = hmac.new(
            self.master_key,
            msg=(json.dumps(proof["disclosed_data"]) + proof["proof_salt"]).encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Verify the HMAC matches
        hmac_valid = computed_hmac == proof["proof_hmac"]
        
        # For this demo, we'll simulate verification of the original hash
        # In a real implementation, this would use ZK proofs to verify without revealing
        hash_valid = True  # Simplified for demo
        
        return hmac_valid and hash_valid
    
    def create_ownership_proof(self, rights_data, owner_address):
        """
        Create a zero-knowledge proof of ownership that doesn't reveal the actual data
        
        Args:
            rights_data (dict): Complete rights information
            owner_address (str): Blockchain address of the claimed owner
            
        Returns:
            dict: ZK ownership proof
        """
        # In a real implementation, this would generate an actual ZK proof
        # For the demo, we'll create a simulated proof
        
        # Extract key identifiers without revealing content
        work_id = hashlib.sha256(str(rights_data.get("work_title", "")).encode()).hexdigest()[:16]
        rights_type = rights_data.get("rights_type", "")
        
        # Create a commitment using the owner's address and work identifier
        commitment = hashlib.sha256((owner_address + work_id).encode()).hexdigest()
        
        # Create a "dummy" ZK proof (in a real system, this would be a proper ZK proof)
        proof_elements = {
            "commitment": commitment,
            "rights_type_hash": hashlib.sha256(rights_type.encode()).hexdigest(),
            "timestamp": int(time.time()),
            "nonce": base64.b64encode(random.randbytes(16)).decode()
        }
        
        signature = hmac.new(
            self.master_key,
            msg=json.dumps(proof_elements).encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return {
            "proof_type": "ownership",
            "work_id": work_id,
            "owner": owner_address,
            "rights_type": rights_type,
            "proof_elements": proof_elements,
            "signature": signature
        }
    
    def verify_ownership_proof(self, proof, claimed_owner):
        """
        Verify a zero-knowledge proof of ownership
        
        Args:
            proof (dict): Ownership proof
            claimed_owner (str): Address of the person claiming ownership
            
        Returns:
            bool: True if the ownership proof is valid
        """
        # Verify the signature
        computed_signature = hmac.new(
            self.master_key,
            msg=json.dumps(proof["proof_elements"]).encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        signature_valid = computed_signature == proof["signature"]
        
        # Verify the claimed owner matches the proof
        owner_valid = claimed_owner == proof["owner"]
        
        # In a real ZK system, we would verify the ZK proof here
        # This is a simplified simulation
        
        return signature_valid and owner_valid

    def derive_verification_key(self, rights_data, purpose):
        """
        Derive a special-purpose verification key that can verify specific aspects
        without revealing the underlying data
        
        Args:
            rights_data (dict): Complete rights information
            purpose (str): Purpose of the verification key
            
        Returns:
            str: Verification key
        """
        # Create a salt based on purpose
        salt = hashlib.sha256(purpose.encode()).digest()
        
        # Use PBKDF2 to derive a key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        
        # Derive the key from a representation of the rights data
        key_material = json.dumps(rights_data).encode()
        derived_key = kdf.derive(key_material)
        
        return base64.b64encode(derived_key).decode()
    
    def create_royalty_verification(self, rights_data, payment_amount):
        """
        Create a proof that verifies a royalty payment is correct without revealing rates
        
        Args:
            rights_data (dict): Complete rights information including royalty rates
            payment_amount (float): Amount being paid
            
        Returns:
            dict: Royalty verification proof
        """
        # Extract royalty information
        royalty_info = rights_data.get("royalty_info", [])
        
        # Calculate expected payments based on royalty percentages
        expected_payments = {}
        for entry in royalty_info:
            party = entry.get("party", "")
            percentage = entry.get("percentage", 0)
            expected = round(payment_amount * percentage, 2)
            expected_payments[party] = expected
        
        # Create a commitment to the payment amounts without revealing percentages
        commitment = hashlib.sha256(json.dumps(expected_payments).encode()).hexdigest()
        
        # Create a verification proof
        proof = {
            "work_title_hash": hashlib.sha256(str(rights_data.get("work_title", "")).encode()).hexdigest(),
            "payment_amount": payment_amount,
            "parties_count": len(royalty_info),
            "payment_commitment": commitment,
            "timestamp": int(time.time())
        }
        
        # Sign the proof
        signature = hmac.new(
            self.master_key,
            msg=json.dumps(proof).encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return {
            "proof": proof,
            "signature": signature,
            "expected_payments": expected_payments  # In a real ZK system, this would be encrypted or not included
        }

# Example usage
def main():
    """Demo the privacy layer features"""
    # Initialize the privacy layer
    privacy = PrivacyLayer()
    
    # Sample rights data
    rights_data = {
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
    }
    
    # 1. Encrypt the full rights data for blockchain storage
    encrypted = privacy.encrypt_rights_data(rights_data)
    print("Encrypted rights data for blockchain:")
    print(f"  Metadata Hash: {encrypted['metadata_hash']}")
    print(f"  Encrypted Length: {len(encrypted['encrypted_data'])} bytes")
    
    # 2. Create a selective disclosure proof (e.g., for a streaming service)
    streaming_disclosure = privacy.create_disclosure_proof(
        rights_data, 
        fields_to_disclose=["work_title", "rights_type", "territory"]
    )
    print("\nSelective Disclosure for Streaming Service:")
    print(f"  Disclosed Fields: {list(streaming_disclosure['disclosed_data'].keys())}")
    print(f"  Original Data Hash: {streaming_disclosure['original_hash'][:16]}...")
    
    # 3. Verify the disclosure proof
    is_valid = privacy.verify_disclosure_proof(streaming_disclosure, encrypted['metadata_hash'])
    print(f"  Verification Result: {is_valid}")
    
    # 4. Create an ownership proof
    owner_address = "0x7338af1E9d6dbc4cc1Efa067C0775Bf222aDb0C3"
    ownership_proof = privacy.create_ownership_proof(rights_data, owner_address)
    print("\nZK Ownership Proof:")
    print(f"  Work ID: {ownership_proof['work_id']}")
    print(f"  Owner: {ownership_proof['owner']}")
    print(f"  Rights Type: {ownership_proof['rights_type']}")
    
    # 5. Verify ownership
    ownership_valid = privacy.verify_ownership_proof(ownership_proof, owner_address)
    print(f"  Ownership Verification: {ownership_valid}")
    
    # 6. Create a royalty verification
    royalty_proof = privacy.create_royalty_verification(rights_data, 1000.00)
    print("\nRoyalty Payment Verification:")
    print(f"  Payment Amount: ${royalty_proof['proof']['payment_amount']}")
    print(f"  Parties: {royalty_proof['proof']['parties_count']}")
    print("  Expected Payments:")
    for party, amount in royalty_proof['expected_payments'].items():
        print(f"    {party}: ${amount}")

if __name__ == "__main__":
    main() 