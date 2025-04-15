import os
import json
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from solcx import compile_standard, install_solc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Blockchain Configuration
WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI", "https://sepolia.base.org")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "")

# Contract addresses
CONTRACT_ADDRESSES = {
    "RightsVault": os.getenv("RIGHTS_VAULT_CONTRACT", "0x0000000000000000000000000000000000000000"),
    "MusicRightsVault": os.getenv("MUSIC_RIGHTS_VAULT_CONTRACT", "0x0000000000000000000000000000000000000000"),
    "VerificationRegistry": os.getenv("VERIFICATION_REGISTRY_CONTRACT", "0x0000000000000000000000000000000000000000"),
    "EnhancedVerification": os.getenv("ENHANCED_VERIFICATION_CONTRACT", "0x0000000000000000000000000000000000000000"),
    "UsageTracker": os.getenv("USAGE_TRACKER_CONTRACT", "0x0000000000000000000000000000000000000000"),
    "RoyaltyManager": os.getenv("ROYALTY_MANAGER_CONTRACT", "0x0000000000000000000000000000000000000000")
}

def compile_contract(contract_name):
    """Compile a specific contract"""
    # Install solc version
    install_solc("0.8.19")
    
    # Get script directory
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    src_dir = project_dir / "src"
    
    # Contract source path
    contract_path = src_dir / f"{contract_name}.sol"
    
    logging.info(f"Compiling contract from {contract_path}")
    
    # Read all Solidity files in the src directory
    sources = {}
    for sol_file in src_dir.glob("*.sol"):
        with open(sol_file, "r") as file:
            sources[sol_file.name] = {"content": file.read()}
    
    # Compile the contract
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": sources,
            "settings": {
                "outputSelection": {
                    "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
                },
                "optimizer": {
                    "enabled": True,
                    "runs": 200
                }
            },
        },
        solc_version="0.8.19",
    )
    
    # Save the compiled contract
    compiled_contract_path = script_dir / f"compiled_{contract_name.lower()}.json"
    with open(compiled_contract_path, "w") as file:
        json.dump(compiled_sol, file)
    
    # Extract contract data
    contract_data = compiled_sol["contracts"][f"{contract_name}.sol"][contract_name]
    abi = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]
    
    # Save ABI separately for easy access
    abi_path = script_dir / f"{contract_name.lower()}_abi.json"
    with open(abi_path, "w") as file:
        json.dump(abi, file, indent=2)
    
    logging.info(f"Contract compiled successfully. ABI saved to {abi_path}")
    
    return abi, bytecode

def deploy_contract(contract_name, constructor_args=None):
    """Deploy a specific contract to Base Sepolia"""
    # Connect to Base Sepolia
    web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))
    
    if not web3.is_connected():
        logging.error(f"Failed to connect to {WEB3_PROVIDER_URI}")
        return
    
    logging.info(f"Connected to Base Sepolia at {WEB3_PROVIDER_URI}")
    
    # Check wallet balance
    if WALLET_ADDRESS:
        balance = web3.eth.get_balance(WALLET_ADDRESS)
        balance_eth = web3.from_wei(balance, 'ether')
        logging.info(f"Wallet balance: {balance_eth} ETH")
    
    # Compile the contract
    abi, bytecode = compile_contract(contract_name)
    
    # Check private key
    if not PRIVATE_KEY:
        logging.error("No private key provided.")
        return
    
    # Ensure private key has 0x prefix
    private_key = PRIVATE_KEY if PRIVATE_KEY.startswith("0x") else "0x" + PRIVATE_KEY
    
    # Create contract
    Contract = web3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Get account from private key
    account = web3.eth.account.from_key(private_key)
    sender_address = account.address
    
    logging.info(f"Deploying {contract_name} from address: {sender_address}")
    
    # Get transaction count (nonce)
    nonce = web3.eth.get_transaction_count(sender_address)
    
    # Build deployment transaction
    if constructor_args:
        transaction = Contract.constructor(*constructor_args).build_transaction(
            {
                "chainId": web3.eth.chain_id,
                "from": sender_address,
                "nonce": nonce,
                "gas": 3000000,
                "gasPrice": web3.eth.gas_price,
            }
        )
    else:
        transaction = Contract.constructor().build_transaction(
            {
                "chainId": web3.eth.chain_id,
                "from": sender_address,
                "nonce": nonce,
                "gas": 3000000,
                "gasPrice": web3.eth.gas_price,
            }
        )
    
    # Sign the transaction
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    
    # Send the transaction
    logging.info(f"Sending {contract_name} deployment transaction...")
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    # Wait for transaction receipt
    logging.info(f"Transaction sent! Hash: {tx_hash.hex()}")
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    # Get contract address
    contract_address = tx_receipt.contractAddress
    
    logging.info(f"{contract_name} deployed successfully to address: {contract_address}")
    
    # Update contract address in our dictionary
    CONTRACT_ADDRESSES[contract_name] = contract_address
    
    # Update .env file with contract address
    env_path = Path(__file__).resolve().parent / ".env"
    with open(env_path, "r") as file:
        env_content = file.read()
    
    # Replace contract address
    env_var_name = f"{contract_name.upper()}_CONTRACT"
    env_content = env_content.replace(
        f"{env_var_name}={os.getenv(env_var_name, '0x0000000000000000000000000000000000000000')}",
        f"{env_var_name}={contract_address}"
    )
    
    with open(env_path, "w") as file:
        file.write(env_content)
    
    logging.info(f"Updated .env file with new {contract_name} contract address: {contract_address}")
    
    return contract_address

def deploy_all_contracts():
    """Deploy all contracts in the correct order with dependencies"""
    # 1. Deploy RightsVault (already deployed)
    rights_vault_address = CONTRACT_ADDRESSES["RightsVault"]
    if rights_vault_address == "0x0000000000000000000000000000000000000000":
        rights_vault_address = deploy_contract("RightsVault")
    
    # 2. Deploy MusicRightsVault (depends on RightsVault)
    music_rights_vault_address = deploy_contract("MusicRightsVault", [rights_vault_address])
    
    # 3. Deploy VerificationRegistry
    verification_registry_address = deploy_contract("VerificationRegistry")
    
    # 4. Deploy EnhancedVerification (depends on RightsVault)
    enhanced_verification_address = deploy_contract("EnhancedVerification", [rights_vault_address])
    
    # 5. Deploy UsageTracker (depends on RightsVault)
    usage_tracker_address = deploy_contract("UsageTracker", [rights_vault_address])
    
    # 6. Deploy RoyaltyManager (depends on RightsVault)
    royalty_manager_address = deploy_contract("RoyaltyManager", [rights_vault_address])
    
    # Save all contract addresses to a JSON file for easy reference
    script_dir = Path(__file__).resolve().parent
    addresses_path = script_dir / "deployed_contracts.json"
    with open(addresses_path, "w") as file:
        json.dump(CONTRACT_ADDRESSES, file, indent=2)
    
    logging.info(f"All contract addresses saved to {addresses_path}")
    
    return CONTRACT_ADDRESSES

if __name__ == "__main__":
    deploy_all_contracts() 