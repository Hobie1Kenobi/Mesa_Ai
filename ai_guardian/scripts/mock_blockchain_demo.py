import json
import logging
import hashlib
from web3 import Web3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
WEB3_PROVIDER_URI = "https://sepolia.base.org"
RIGHTS_VAULT_CONTRACT = "0x7338af1E9d6dbc4cc1Efa067C0775Bf222aDb0C3"

def simulate_blockchain_interaction(contract_params):
    """Simulates calling the smart contract function."""
    if not contract_params:
        logging.warning("  Skipping blockchain interaction due to missing params.")
        return
        
    logging.info(f"Simulating blockchain interaction for rightId: {contract_params['rightId']}")
    print("--- Blockchain Call Simulation ---")
    print(f"  Target Contract: MusicRightsVault")
    print(f"  Function: registerRight")
    print(f"  Parameters:")
    print(f"    rightId: {contract_params['rightId']}")
    print(f"    encryptedData: {contract_params['encryptedData'][:64]}... (truncated)")
    print(f"    metadataHash: {contract_params['metadataHash']}")
    print(f"  Display Data:")
    for key, value in contract_params["display"].items():
        print(f"    {key}: {value}")
    print("----------------------------------")

def prepare_smart_contract_tx(filename, extracted_info):
    """Prepares smart contract transaction data based on extracted info."""
    logging.info(f"Preparing smart contract transaction for {filename}")
    
    right_id = hashlib.sha256(filename.encode()).hexdigest()[:16] 
    right_id_bytes32 = "0x" + right_id.ljust(64, '0')  # Convert to bytes32 format for blockchain
    
    # Get rights holder information
    rights_holder_name = extracted_info.get('publisher_party', extracted_info.get('artist_party', 'Unknown Holder'))
    rights_holder_address = "0x1111111111111111111111111111111111111111"  # Mock address
    
    # Get rights type
    rights_type = extracted_info.get('rights_type', 'Publishing')
    
    # Get territory
    territory = extracted_info.get('territory', 'Global')
    
    # Extract dates
    effective_date = extracted_info.get('effective_date', '')
    
    # Extract percentage
    percentage = 0
    if 'royalty_info' in extracted_info and isinstance(extracted_info['royalty_info'], list):
        for royalty in extracted_info['royalty_info']:
            if isinstance(royalty, dict) and 'party' in royalty and royalty['party'] == rights_holder_name:
                if 'percentage' in royalty and royalty['percentage'] is not None:
                    percentage = int(float(royalty['percentage']) * 100)
                    break
    
    # Prepare data for blockchain storage
    contract_data = {
        "original_filename": filename,
        "work_title": extracted_info.get('work_title', ""),
        "term_description": extracted_info.get('term', ""),
        "rights_holder": rights_holder_name,
        "rights_type": rights_type,
        "territory": territory,
        "percentage": percentage,
        "start_date": effective_date,
        "end_date": "",
        "raw_extracted_info": json.dumps(extracted_info, default=str)
    }
    
    # In a real implementation, we would encrypt this data with the user's public key
    # For now, we'll just convert it to a hexadecimal string for the smart contract
    encrypted_data = Web3.to_hex(text=json.dumps(contract_data))
    
    web3 = Web3()  # Create a Web3 instance without a provider just for hashing
    metadata_hash = web3.keccak(text=json.dumps(contract_data, sort_keys=True)).hex()

    params = {
        "rightId": right_id_bytes32,
        "encryptedData": encrypted_data,
        "metadataHash": metadata_hash
    }
    
    # Add auxiliary data for display purposes and simulation
    params["display"] = {
        "rightsHolder": rights_holder_name,
        "rightsType": rights_type,
        "percentage": percentage,
        "territory": territory,
        "startDate": effective_date,
        "endDate": ""
    }
    
    return params

def main():
    """Mock blockchain integration demo with hardcoded contract data."""
    logging.info("--- AI Guardian Mock Blockchain Integration Demo ---")
    
    # Define mock contract data for demonstration
    mock_contracts = [
        {
            "filename": "Music_Producer_Contract_Template.txt",
            "data": {
                "artist_party": "Sarah Wilson",
                "publisher_party": "Dreamlight Records",
                "work_title": "Album: Midnight Dreams Collection",
                "rights_type": "Publishing",
                "territory": "Global",
                "term": "1 year with option to renew",
                "royalty_info": [
                    {"party": "Sarah Wilson", "percentage": 0.5},
                    {"party": "Dreamlight Records", "percentage": 0.5}
                ],
                "effective_date": "2025-04-05"
            }
        },
        {
            "filename": "performance_agrmt.txt",
            "data": {
                "artist_party": "The Lunar Echoes",
                "publisher_party": "Skyline Arena Entertainment LLC",
                "work_title": "Live Performance at Skyline Arena",
                "rights_type": "Performance",
                "territory": "Las Vegas, Nevada",
                "term": "2 weeks with extension options",
                "royalty_info": [
                    {"party": "The Lunar Echoes", "percentage": 0.75},
                    {"party": "Skyline Arena Entertainment LLC", "percentage": 0.25}
                ],
                "effective_date": "2025-05-15"
            }
        },
        {
            "filename": "ComposerExclusiveSample.txt",
            "data": {
                "artist_party": "Daniel Morgan",
                "publisher_party": "Harmonic Bridge Publishing Group",
                "work_title": "Various Compositions",
                "rights_type": "Publishing",
                "territory": "Global",
                "term": "3 years with renewal options",
                "royalty_info": [
                    {"party": "Daniel Morgan", "percentage": 0.5},
                    {"party": "Harmonic Bridge Publishing Group", "percentage": 0.5}
                ],
                "effective_date": "2025-03-18"
            }
        },
        {
            "filename": "Co-publisher_agreement.txt",
            "data": {
                "artist_party": "Emma Wilson Music, LLC",
                "publisher_party": "Stellar Sound Publishing Inc.",
                "work_title": "Five Original Compositions",
                "rights_type": "Publishing",
                "territory": "Global",
                "term": "Life of Copyright",
                "royalty_info": [
                    {"party": "Emma Wilson Music, LLC", "percentage": 0.5},
                    {"party": "Stellar Sound Publishing Inc.", "percentage": 0.5}
                ],
                "effective_date": "2025-04-10"
            }
        }
    ]
    
    # Process each mock contract
    for contract in mock_contracts:
        filename = contract["filename"]
        extracted_info = contract["data"]
        
        logging.info(f"--- Processing Document: {filename} ---")
        logging.info(f"  Using mock data for demonstration")
        
        # Log the extracted information
        logging.info(f"  Extracted Info: {json.dumps(extracted_info, indent=2)}")
        
        # Prepare smart contract transaction based on extracted info
        tx_params = prepare_smart_contract_tx(filename, extracted_info)
        
        if not tx_params:
            continue
        
        # Simulate blockchain interaction
        logging.info("  Running in simulation mode for demonstration")
        simulate_blockchain_interaction(tx_params)
    
    logging.info("--- Demo Pipeline Finished ---")

if __name__ == "__main__":
    main() 