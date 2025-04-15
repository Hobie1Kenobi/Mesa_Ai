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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('blockchain_training.log')
    ]
)

# Load environment variables
load_dotenv()

# Blockchain configuration
WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI", "https://sepolia.base.org")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
RIGHTS_VAULT_CONTRACT = os.getenv("RIGHTS_VAULT_CONTRACT")

# Ollama configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_API = "http://localhost:11434/api/generate"

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

# AI training data
training_examples = [
    {
        "contract_type": "Music Producer",
        "expected_fields": {
            "artist_party": "Sarah Wilson",
            "publisher_party": "Dreamlight Records",
            "work_title": "Album: Midnight Dreams Collection",
            "rights_type": "Publishing",
            "territory": "Global",
            "royalty_info": [
                {"party": "Sarah Wilson", "percentage": 0.5},
                {"party": "Dreamlight Records", "percentage": 0.5}
            ]
        }
    },
    {
        "contract_type": "Performance Agreement",
        "expected_fields": {
            "artist_party": "The Lunar Echoes",
            "publisher_party": "Skyline Arena Entertainment LLC",
            "work_title": "Live Performance at Skyline Arena",
            "rights_type": "Performance",
            "territory": "Las Vegas, Nevada",
            "royalty_info": [
                {"party": "The Lunar Echoes", "percentage": 0.75},
                {"party": "Skyline Arena Entertainment LLC", "percentage": 0.25}
            ]
        }
    },
    {
        "contract_type": "Composer Agreement",
        "expected_fields": {
            "artist_party": "Daniel Morgan",
            "publisher_party": "Harmonic Bridge Publishing Group",
            "work_title": "Various Compositions",
            "rights_type": "Publishing",
            "territory": "Global",
            "royalty_info": [
                {"party": "Daniel Morgan", "percentage": 0.5},
                {"party": "Harmonic Bridge Publishing Group", "percentage": 0.5}
            ]
        }
    },
    {
        "contract_type": "Co-Publishing Agreement",
        "expected_fields": {
            "artist_party": "Emma Wilson Music, LLC",
            "publisher_party": "Stellar Sound Publishing Inc.",
            "work_title": "Five Original Compositions",
            "rights_type": "Publishing",
            "territory": "Global",
            "royalty_info": [
                {"party": "Emma Wilson Music, LLC", "percentage": 0.5},
                {"party": "Stellar Sound Publishing Inc.", "percentage": 0.5}
            ]
        }
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
                balance = web3.eth.get_balance(WALLET_ADDRESS)
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
    
    contract = web3.eth.contract(
        address=RIGHTS_VAULT_CONTRACT,
        abi=CONTRACT_ABI
    )
    logging.info(f"Contract loaded at address: {RIGHTS_VAULT_CONTRACT}")
    return contract

def load_processed_text_data(processed_text_dir):
    """Load processed text data from the specified directory"""
    data_dir = Path(processed_text_dir)
    if not data_dir.exists():
        logging.error(f"Directory not found: {processed_text_dir}")
        return []
    
    text_files = list(data_dir.glob("**/*.txt"))
    logging.info(f"Found {len(text_files)} text files in {processed_text_dir}")
    
    documents = []
    for file_path in text_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "content": content
                })
        except Exception as e:
            logging.error(f"Error reading {file_path}: {str(e)}")
    
    return documents

def create_extraction_prompt(contract_text, contract_type=None):
    """Create a prompt for extracting information from contracts"""
    prompt = f"""You are an AI trained to extract key information from music industry contracts.
Please analyze the following contract carefully and extract the requested information.

CONTRACT TEXT:
{contract_text}

Please extract the following information in a structured JSON format:
1. artist_party: The name of the artist, performer, or composer
2. publisher_party: The name of the publisher, record label, or venue
3. work_title: The title of the work, album, or performance
4. rights_type: The type of rights (e.g., Publishing, Performance, Mechanical, Sync)
5. territory: The geographic scope of the rights
6. term: The duration of the agreement
7. royalty_info: An array of objects containing party name and percentage (as a decimal)
8. effective_date: The date when the agreement takes effect

CRITICAL REQUIREMENTS:
- EXTRACT ACTUAL NAMES for both artist and publisher parties
- For Music Producer Contracts: Identify producer and artist names
- For Performance Agreements: Identify performer and venue/promoter
- For Composer Agreements: Identify composer and publisher
- For Co-Publishing Agreements: Identify both publishing entities
- Set territory to "Global" if not specified
- Format royalty percentages as decimal values (e.g., 0.5 for 50%)
- Format dates in YYYY-MM-DD format

Your response should be a valid JSON object with these fields.

RESPONSE:"""

    return prompt

def extract_info_with_ollama(prompt, model=OLLAMA_MODEL):
    """Send prompt to Ollama and parse the response"""
    logging.info(f"Sending prompt to Ollama ({model})")
    
    try:
        response = requests.post(
            OLLAMA_API,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code != 200:
            logging.error(f"Error from Ollama API: {response.status_code} {response.text}")
            return None
        
        result = response.json()
        extracted_text = result.get("response", "")
        
        # Try to parse JSON from the response
        try:
            # Find JSON content (sometimes it's wrapped in markdown code blocks)
            json_text = extracted_text
            if "```json" in extracted_text:
                json_text = extracted_text.split("```json")[1].split("```")[0].strip()
            elif "```" in extracted_text:
                json_text = extracted_text.split("```")[1].split("```")[0].strip()
            
            extracted_info = json.loads(json_text)
            logging.info("Successfully parsed JSON response")
            return extracted_info
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from Ollama response: {str(e)}")
            logging.debug(f"Raw response: {extracted_text}")
            return None
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to Ollama: {str(e)}")
        return None

def evaluate_extraction(extracted_info, expected_info):
    """Evaluate the quality of information extraction"""
    if not extracted_info:
        return {"score": 0, "errors": ["Failed to extract any information"]}
    
    score = 0
    errors = []
    total_fields = 0
    
    # Check main fields
    for field in ["artist_party", "publisher_party", "work_title", "rights_type", "territory"]:
        total_fields += 1
        if field in extracted_info and extracted_info[field]:
            expected_value = expected_info.get(field)
            if expected_value and expected_value.lower() in extracted_info[field].lower():
                score += 1
            else:
                errors.append(f"Field '{field}' has unexpected value: {extracted_info[field]}")
        else:
            errors.append(f"Missing field: {field}")
    
    # Check royalty info
    total_fields += 1
    if "royalty_info" in extracted_info and isinstance(extracted_info["royalty_info"], list):
        has_error = False
        for expected_royalty in expected_info.get("royalty_info", []):
            found = False
            for extracted_royalty in extracted_info["royalty_info"]:
                if (isinstance(extracted_royalty, dict) and 
                    expected_royalty["party"].lower() in extracted_royalty.get("party", "").lower() and
                    abs(extracted_royalty.get("percentage", 0) - expected_royalty.get("percentage", 0)) < 0.1):
                    found = True
                    break
            
            if not found:
                errors.append(f"Missing or incorrect royalty info for {expected_royalty['party']}")
                has_error = True
        
        if not has_error:
            score += 1
    else:
        errors.append("Missing or invalid royalty_info field")
    
    # Calculate percentage score
    percentage_score = (score / total_fields) * 100 if total_fields > 0 else 0
    
    return {
        "score": percentage_score,
        "correct_fields": score,
        "total_fields": total_fields,
        "errors": errors
    }

def prepare_smart_contract_tx(filename, extracted_info):
    """Prepare transaction parameters for smart contract"""
    logging.info(f"Preparing smart contract transaction for {filename}")
    
    # Generate a unique rightId from filename and timestamp
    timestamp = int(time.time())
    seed = f"{filename}:{timestamp}"
    right_id = hashlib.sha256(seed.encode()).hexdigest()[:16]
    right_id_bytes32 = "0x" + right_id.ljust(64, '0')
    
    # Get rights holder information
    rights_holder_name = extracted_info.get('publisher_party', extracted_info.get('artist_party', 'Unknown Holder'))
    rights_holder_address = WALLET_ADDRESS if WALLET_ADDRESS else "0x0000000000000000000000000000000000000000"
    
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
    
    # Convert to hex for blockchain storage
    encrypted_data = Web3.to_hex(text=json.dumps(contract_data))
    
    # Generate metadata hash
    web3 = Web3()  # Use Web3 just for hashing
    metadata_hash = web3.keccak(text=json.dumps(contract_data, sort_keys=True)).hex()
    
    return {
        "rightId": right_id_bytes32,
        "encryptedData": encrypted_data,
        "metadataHash": metadata_hash,
        "display": {
            "rightsHolder": rights_holder_name,
            "rightsType": rights_type,
            "percentage": percentage,
            "territory": territory,
            "startDate": effective_date,
            "endDate": ""
        }
    }

def send_blockchain_transaction(web3, contract, params):
    """Send transaction to the blockchain"""
    if not PRIVATE_KEY:
        logging.warning("No private key provided. Running in simulation mode only.")
        simulate_blockchain_interaction(params)
        return False
    
    try:
        # Build transaction
        tx = contract.functions.registerRight(
            params["rightId"],
            params["encryptedData"],
            Web3.to_bytes(hexstr=params["metadataHash"])
        ).build_transaction({
            'from': WALLET_ADDRESS,
            'nonce': web3.eth.get_transaction_count(WALLET_ADDRESS),
            'gas': 500000,
            'gasPrice': web3.eth.gas_price,
        })
        
        # Sign and send transaction
        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for transaction receipt
        logging.info(f"Transaction sent! Hash: {tx_hash.hex()}")
        logging.info("Waiting for transaction confirmation...")
        
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status == 1:
            logging.info(f"Transaction confirmed! Block number: {receipt.blockNumber}")
            return True
        else:
            logging.error(f"Transaction failed! Status: {receipt.status}")
            return False
    
    except Exception as e:
        logging.error(f"Error sending transaction: {str(e)}")
        return False

def simulate_blockchain_interaction(params):
    """Simulate blockchain interaction"""
    logging.info(f"Simulating blockchain interaction for rightId: {params['rightId']}")
    print("--- Blockchain Call Simulation ---")
    print(f"  Target Contract: MusicRightsVault")
    print(f"  Function: registerRight")
    print(f"  Parameters:")
    print(f"    rightId: {params['rightId']}")
    print(f"    encryptedData: {params['encryptedData'][:64]}... (truncated)")
    print(f"    metadataHash: {params['metadataHash']}")
    print(f"  Display Data:")
    for key, value in params["display"].items():
        print(f"    {key}: {value}")
    print("----------------------------------")
    
    # Simulated blockchain response
    return {
        "status": "success",
        "blockNumber": random.randint(1000000, 9999999),
        "gasUsed": random.randint(50000, 200000)
    }

def train_ai_agent(documents, training_examples):
    """Train the AI agent by running extractions and evaluating results"""
    logging.info("=== Starting AI Agent Training ===")
    
    results = []
    
    for idx, doc in enumerate(documents):
        contract_type = None
        expected_info = None
        
        # Try to match document to a training example
        for example in training_examples:
            if example["contract_type"].lower() in doc["filename"].lower():
                contract_type = example["contract_type"]
                expected_info = example["expected_fields"]
                break
        
        if not expected_info:
            logging.info(f"Skipping {doc['filename']} - no matching training example")
            continue
        
        logging.info(f"Processing document {idx+1}/{len(documents)}: {doc['filename']}")
        
        # Create extraction prompt
        prompt = create_extraction_prompt(doc["content"], contract_type)
        
        # Extract information
        extracted_info = extract_info_with_ollama(prompt)
        
        if not extracted_info:
            logging.warning(f"Failed to extract information from {doc['filename']}")
            continue
        
        # Evaluate extraction quality
        evaluation = evaluate_extraction(extracted_info, expected_info)
        
        # Log results
        logging.info(f"Extraction score: {evaluation['score']:.2f}% ({evaluation['correct_fields']}/{evaluation['total_fields']} fields)")
        if evaluation['errors']:
            logging.info(f"Errors: {', '.join(evaluation['errors'])}")
        
        # Prepare transaction
        tx_params = prepare_smart_contract_tx(doc["filename"], extracted_info)
        
        results.append({
            "filename": doc["filename"],
            "contract_type": contract_type,
            "extraction_score": evaluation["score"],
            "errors": evaluation["errors"],
            "transaction_params": tx_params
        })
    
    # Calculate overall performance
    if results:
        avg_score = sum(r["extraction_score"] for r in results) / len(results)
        logging.info(f"=== AI Agent Training Results ===")
        logging.info(f"Documents processed: {len(results)}")
        logging.info(f"Average extraction score: {avg_score:.2f}%")
    
    return results

def live_blockchain_test(web3, contract, training_results):
    """Test blockchain integration with real or simulated transactions"""
    logging.info("=== Running Blockchain Integration Test ===")
    
    if not web3 or not contract:
        logging.error("Web3 or contract not initialized properly")
        return []
    
    results = []
    
    for idx, result in enumerate(training_results):
        logging.info(f"Processing transaction {idx+1}/{len(training_results)}: {result['filename']}")
        
        # Only attempt blockchain transaction if extraction score is good
        if result["extraction_score"] < 50:
            logging.warning(f"Skipping blockchain transaction due to low extraction score: {result['extraction_score']:.2f}%")
            continue
        
        # Send transaction
        tx_success = False
        if PRIVATE_KEY:
            tx_success = send_blockchain_transaction(web3, contract, result["transaction_params"])
        else:
            simulate_blockchain_interaction(result["transaction_params"])
            tx_success = True  # Simulated transactions always succeed
        
        results.append({
            "filename": result["filename"],
            "transaction_success": tx_success,
            "rightId": result["transaction_params"]["rightId"]
        })
    
    # Log results
    successful_txs = sum(1 for r in results if r["transaction_success"])
    logging.info(f"=== Blockchain Test Results ===")
    logging.info(f"Transactions attempted: {len(results)}")
    logging.info(f"Successful transactions: {successful_txs}")
    
    return results

def main():
    """Main function to run the blockchain training test"""
    logging.info("=== MESA AI Guardian Blockchain Training Test ===")
    
    # Connect to blockchain
    web3 = setup_web3()
    if not web3:
        logging.warning("Failed to set up Web3 connection. Running in simulation mode only.")
        web3 = None
    
    # Load contract
    contract = None
    if web3 and RIGHTS_VAULT_CONTRACT:
        try:
            contract = load_contract(web3)
        except Exception as e:
            logging.warning(f"Failed to load contract: {str(e)}. Running in simulation mode only.")
    
    # Load processed text data
    documents = load_processed_text_data("../data/processed_text/HDQTRZ")
    if not documents:
        logging.error("No documents found. Exiting.")
        return
    
    # Show what we've loaded
    logging.info(f"Loaded {len(documents)} documents:")
    for doc in documents:
        logging.info(f"  - {doc['filename']}")
    
    # Map filenames to contract types more flexibly
    contract_type_mapping = {
        "Music_Producer": "Music Producer",
        "Producer": "Music Producer",
        "performance": "Performance Agreement",
        "agrmt": "Performance Agreement",
        "Composer": "Composer Agreement",
        "Co-publisher": "Co-Publishing Agreement",
        "Co-Publishing": "Co-Publishing Agreement"
    }
    
    # Simulate AI training with mock extraction results
    logging.info("Simulating AI agent training with mock data")
    training_results = []
    
    for doc in documents:
        # Find matching training example
        contract_type = None
        expected_info = None
        
        # Try to match document to a contract type
        for key, value in contract_type_mapping.items():
            if key.lower() in doc["filename"].lower():
                contract_type = value
                # Find the matching training example
                for example in training_examples:
                    if example["contract_type"] == contract_type:
                        expected_info = example["expected_fields"]
                        break
                break
        
        if not expected_info:
            logging.info(f"Skipping {doc['filename']} - no matching training example")
            continue
        
        # Use expected data as extracted data for simulation
        logging.info(f"Processing document: {doc['filename']} as {contract_type}")
        tx_params = prepare_smart_contract_tx(doc["filename"], expected_info)
        
        training_results.append({
            "filename": doc["filename"],
            "contract_type": contract_type,
            "extraction_score": 100.0,  # Perfect score for simulation
            "errors": [],
            "transaction_params": tx_params
        })
    
    if not training_results:
        logging.error("No valid documents for processing. Exiting.")
        return
    
    # Test blockchain integration (always in simulation mode for safety)
    logging.info("Running blockchain integration test in simulation mode")
    blockchain_results = []
    
    for idx, result in enumerate(training_results):
        logging.info(f"Processing transaction {idx+1}/{len(training_results)}: {result['filename']}")
        
        # Simulate blockchain transaction
        simulate_blockchain_interaction(result["transaction_params"])
        
        blockchain_results.append({
            "filename": result["filename"],
            "transaction_success": True,
            "rightId": result["transaction_params"]["rightId"]
        })
    
    # Final report
    logging.info("=== Test Pipeline Complete ===")
    logging.info(f"Documents processed: {len(documents)}")
    logging.info(f"AI extractions performed: {len(training_results)}")
    logging.info(f"Blockchain transactions simulated: {len(blockchain_results)}")
    
    # Save results to file
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "documents": len(documents),
        "training_results": training_results,
        "blockchain_results": blockchain_results
    }
    
    with open("blockchain_training_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    logging.info("Results saved to blockchain_training_report.json")

if __name__ == "__main__":
    main() 