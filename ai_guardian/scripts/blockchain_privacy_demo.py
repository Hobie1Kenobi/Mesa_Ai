import os
import json
import logging
import hashlib
import random
import time
from web3 import Web3
from dotenv import load_dotenv
import requests
from pathlib import Path
from privacy_layer import PrivacyLayer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('blockchain_privacy.log')
    ]
)

# Load environment variables
load_dotenv()

# Blockchain configuration
WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI", "https://sepolia.base.org")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "0x7338af1E9d6dbc4cc1Efa067C0775Bf222aDb0C3")
RIGHTS_VAULT_CONTRACT = os.getenv("RIGHTS_VAULT_CONTRACT", "0x7338af1E9d6dbc4cc1Efa067C0775Bf222aDb0C3")

# Contract ABI - Simplified for this example
CONTRACT_ABI = [
    {
        "inputs": [
            {"name": "rightId", "type": "bytes32"},
            {"name": "encryptedData", "type": "bytes"},
            {"name": "metadataHash", "type": "bytes32"}
        ],
        "name": "registerRight",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "rightId", "type": "bytes32"}],
        "name": "getRightMetadata",
        "outputs": [{"name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Sample Music Rights Data
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

def setup_web3():
    """Set up Web3 connection to Base Sepolia"""
    web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))
    
    try:
        connected = web3.is_connected()
        if not connected:
            logging.error(f"Failed to connect to {WEB3_PROVIDER_URI}")
            return None
        
        logging.info(f"Connected to {WEB3_PROVIDER_URI}")
        
        try:
            block_number = web3.eth.block_number
            logging.info(f"Current block number: {block_number}")
        except Exception as e:
            logging.warning(f"Could not get block number: {str(e)}")
        
        if WALLET_ADDRESS:
            try:
                # Convert to checksum address
                checksum_address = Web3.to_checksum_address(WALLET_ADDRESS)
                balance = web3.eth.get_balance(checksum_address)
                eth_balance = web3.from_wei(balance, 'ether')
                logging.info(f"Wallet balance: {eth_balance} ETH")
            except Exception as e:
                logging.warning(f"Could not get wallet balance: {str(e)}")
        
        return web3
    except Exception as e:
        logging.error(f"Error setting up Web3: {str(e)}")
        return None

def load_contract(web3):
    """Load the smart contract instance"""
    if not RIGHTS_VAULT_CONTRACT:
        logging.error("Rights vault contract address not provided")
        return None
    
    try:
        # Convert to checksum address
        contract_address = Web3.to_checksum_address(RIGHTS_VAULT_CONTRACT)
        contract = web3.eth.contract(
            address=contract_address,
            abi=CONTRACT_ABI
        )
        logging.info(f"Contract loaded at address: {contract_address}")
        return contract
    except Exception as e:
        logging.error(f"Error loading contract: {str(e)}")
        return None

def prepare_blockchain_rights_registration(rights_data, privacy_layer):
    """
    Prepare rights data for blockchain registration with privacy features
    
    Args:
        rights_data (dict): Music rights information
        privacy_layer (PrivacyLayer): Privacy layer instance
        
    Returns:
        dict: Transaction parameters for blockchain
    """
    # Generate a unique rightId from work title and timestamp
    timestamp = int(time.time())
    seed = f"{rights_data['work_title']}:{timestamp}"
    right_id = hashlib.sha256(seed.encode()).hexdigest()[:16]
    right_id_bytes32 = "0x" + right_id.ljust(64, '0')
    
    # Encrypt the rights data with privacy layer
    encrypted_package = privacy_layer.encrypt_rights_data(rights_data)
    encrypted_data = encrypted_package["encrypted_data"]
    metadata_hash = encrypted_package["metadata_hash"]
    
    return {
        "rightId": right_id_bytes32,
        "encryptedData": "0x" + encrypted_data,
        "metadataHash": "0x" + metadata_hash,
        "display": {
            "workTitle": rights_data.get("work_title", ""),
            "rightsHolder": rights_data.get("publisher_party", ""),
            "rightsType": rights_data.get("rights_type", ""),
            "territory": rights_data.get("territory", "")
        }
    }

def simulate_blockchain_registration(params):
    """Simulate blockchain registration"""
    logging.info(f"Simulating blockchain registration for {params['display']['workTitle']}")
    print(f"\n--- Registering Rights for '{params['display']['workTitle']}' ---")
    print(f"  Right ID: {params['rightId']}")
    print(f"  Rights Holder: {params['display']['rightsHolder']}")
    print(f"  Rights Type: {params['display']['rightsType']}")
    print(f"  Territory: {params['display']['territory']}")
    print(f"  Encrypted Data Length: {len(params['encryptedData']) if params['encryptedData'].startswith('0x') else len('0x' + params['encryptedData'])} bytes")
    print(f"  Metadata Hash: {params['metadataHash']}")
    
    # Simulated blockchain response
    return {
        "status": "success",
        "blockNumber": random.randint(1000000, 9999999),
        "gasUsed": random.randint(50000, 200000),
        "txHash": "0x" + ''.join(random.choices('0123456789abcdef', k=64))
    }

def verify_right_on_blockchain(right_id, expected_metadata_hash):
    """
    Simulated verification of rights existence on blockchain
    
    Args:
        right_id (str): Identifier for the right
        expected_metadata_hash (str): Expected hash for verification
        
    Returns:
        bool: True if verified
    """
    # In a real implementation, this would query the blockchain
    # For the demo, we'll simulate a successful verification
    logging.info(f"Verifying right {right_id} on blockchain")
    return True

def demo_privacy_features(rights_data, privacy_layer, blockchain_params):
    """
    Demonstrate privacy features after blockchain registration
    
    Args:
        rights_data (dict): Original rights data
        privacy_layer (PrivacyLayer): Privacy layer instance
        blockchain_params (dict): Blockchain registration parameters
    """
    right_id = blockchain_params["rightId"]
    metadata_hash = blockchain_params["metadataHash"].replace("0x", "")
    
    print(f"\n=== Privacy Features Demo for '{rights_data['work_title']}' ===")
    
    # 1. Selective Disclosure for a Streaming Platform
    print("\n1. Selective Disclosure for Streaming Platform")
    print("   A streaming service needs to verify distribution rights without seeing royalty details")
    
    streaming_fields = ["work_title", "rights_type", "territory", "effective_date"]
    streaming_disclosure = privacy_layer.create_disclosure_proof(
        rights_data, 
        fields_to_disclose=streaming_fields
    )
    
    print(f"   Disclosed Fields: {streaming_fields}")
    print("   Disclosed Data:")
    for field, value in streaming_disclosure["disclosed_data"].items():
        print(f"     - {field}: {value}")
    
    # Verify the disclosure
    streaming_valid = privacy_layer.verify_disclosure_proof(streaming_disclosure, metadata_hash)
    print(f"   Verification Result: {streaming_valid}")
    
    # 2. Ownership Proof for Rights Claim
    print("\n2. Zero-Knowledge Ownership Proof")
    print("   Artist proving ownership without revealing contract details")
    
    owner_address = WALLET_ADDRESS
    ownership_proof = privacy_layer.create_ownership_proof(rights_data, owner_address)
    
    print(f"   Work ID: {ownership_proof['work_id']}")
    print(f"   Rights Type: {ownership_proof['rights_type']}")
    print(f"   Proof Type: {ownership_proof['proof_type']}")
    
    # Verify the ownership
    ownership_valid = privacy_layer.verify_ownership_proof(ownership_proof, owner_address)
    print(f"   Ownership Verification: {ownership_valid}")
    
    # 3. Royalty Verification
    print("\n3. Royalty Payment Verification")
    print("   Verifying correct payment amounts without revealing full royalty rates")
    
    payment_amount = 10000.00  # Example payment of $10,000
    royalty_proof = privacy_layer.create_royalty_verification(rights_data, payment_amount)
    
    print(f"   Payment Amount: ${royalty_proof['proof']['payment_amount']}")
    print(f"   Parties: {royalty_proof['proof']['parties_count']}")
    print("   Expected Payments:")
    for party, amount in royalty_proof['expected_payments'].items():
        print(f"     - {party}: ${amount}")
    
    print("\n   This allows verification that payments match contractual rates")
    print("   without revealing the specific percentages to external parties")

def main():
    """Main function to run the blockchain privacy demo"""
    logging.info("=== MESA Rights Vault Blockchain Privacy Demo ===")
    
    # Initialize the privacy layer
    privacy_layer = PrivacyLayer()
    logging.info("Privacy layer initialized")
    
    # Connect to blockchain (or run in simulation mode)
    web3 = setup_web3()
    if not web3:
        logging.warning("Failed to set up Web3 connection. Running in simulation mode only.")
    
    # Initialize contract (optional for simulation)
    contract = None
    if web3:
        contract = load_contract(web3)
        if not contract:
            logging.warning("Failed to load contract. Running in simulation mode only.")
    
    # Process each rights entry
    logging.info(f"Processing {len(SAMPLE_RIGHTS)} sample rights entries")
    
    for idx, rights_data in enumerate(SAMPLE_RIGHTS):
        logging.info(f"Processing rights entry {idx+1}/{len(SAMPLE_RIGHTS)}: {rights_data['work_title']}")
        
        # Prepare for blockchain registration
        blockchain_params = prepare_blockchain_rights_registration(rights_data, privacy_layer)
        
        # Simulate blockchain registration
        tx_result = simulate_blockchain_registration(blockchain_params)
        
        # Demonstrate privacy features
        demo_privacy_features(rights_data, privacy_layer, blockchain_params)
    
    # Summary
    print("\n=== MESA Rights Vault Demo Summary ===")
    print(f"Rights entries processed: {len(SAMPLE_RIGHTS)}")
    print("Privacy features demonstrated:")
    print("  1. End-to-end encryption for blockchain storage")
    print("  2. Selective disclosure for different platforms")
    print("  3. Zero-knowledge ownership proofs")
    print("  4. Privacy-preserving royalty verification")
    print("\nThese features enable artists to maintain control over their sensitive")
    print("contract information while still providing necessary verification")
    print("capabilities to different industry participants.")

if __name__ == "__main__":
    main() 