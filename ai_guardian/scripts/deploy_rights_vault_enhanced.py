#!/usr/bin/env python3

from web3 import Web3
import json
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path)

# Connect to Base Sepolia
BASE_SEPOLIA_RPC_URL = os.getenv("BASE_SEPOLIA_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")

if not all([BASE_SEPOLIA_RPC_URL, PRIVATE_KEY, WALLET_ADDRESS]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

w3 = Web3(Web3.HTTPProvider(BASE_SEPOLIA_RPC_URL))

# Set up account
account = w3.eth.account.from_key(PRIVATE_KEY)
w3.eth.default_account = account.address

def deploy_contract(contract_name, *args):
    """Deploy a contract from the compiled JSON file"""
    contracts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'contracts')
    build_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'build')
    
    # Load contract JSON (would normally come from a compiler)
    with open(os.path.join(build_dir, f'{contract_name}.json'), 'r') as f:
        contract_json = json.load(f)
    
    # Create contract
    contract = w3.eth.contract(
        abi=contract_json['abi'],
        bytecode=contract_json['bytecode']
    )
    
    # Build constructor transaction
    constructor_txn = contract.constructor(*args).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 2000000,  # Adjust gas limit as needed
        'gasPrice': w3.eth.gas_price
    })
    
    # Sign transaction
    signed_txn = w3.eth.account.sign_transaction(constructor_txn, PRIVATE_KEY)
    
    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Deployment transaction sent: {tx_hash.hex()}")
    
    # Wait for transaction to be mined
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Contract deployed at: {tx_receipt.contractAddress}")
    
    # Return contract instance
    return w3.eth.contract(address=tx_receipt.contractAddress, abi=contract_json['abi'])

def simulate_deployment():
    """Deploy all contracts to Base Sepolia"""
    print("\n=== Deploying Contracts to Base Sepolia ===")
    print(f"Using account: {account.address}")
    print(f"Network: {BASE_SEPOLIA_RPC_URL}")
    
    try:
        # Check balance
        balance = w3.eth.get_balance(account.address)
        print(f"Account balance: {w3.from_wei(balance, 'ether')} ETH")
        
        if balance == 0:
            raise ValueError("Account has no ETH. Please fund your account with Base Sepolia ETH.")
        
        print("\nDeploying contracts...")
        
        print("1. Deploying RightsVault...")
        rights_vault = deploy_contract('RightsVault')
        
        print("\n2. Deploying MusicRightsVault...")
        music_rights_vault = deploy_contract('MusicRightsVault', rights_vault.address)
        
        print("\n3. Deploying VerificationRegistry...")
        verification_registry = deploy_contract('VerificationRegistry')
        
        print("\n4. Deploying EnhancedVerification...")
        enhanced_verification = deploy_contract('EnhancedVerification', rights_vault.address)
        
        print("\n5. Deploying UsageTracker...")
        usage_tracker = deploy_contract('UsageTracker', rights_vault.address)
        
        print("\n6. Deploying RoyaltyManager...")
        royalty_manager = deploy_contract('RoyaltyManager', rights_vault.address)
        
        # Save deployed addresses
        deployed_contracts = {
            'RightsVault': rights_vault.address,
            'MusicRightsVault': music_rights_vault.address,
            'VerificationRegistry': verification_registry.address,
            'EnhancedVerification': enhanced_verification.address,
            'UsageTracker': usage_tracker.address,
            'RoyaltyManager': royalty_manager.address
        }
        
        # Save to JSON file
        with open(os.path.join(os.path.dirname(__file__), 'deployed_contracts.json'), 'w') as f:
            json.dump(deployed_contracts, f, indent=2)
        
        print("\n=== Deployment Complete ===")
        print("Contract addresses saved to deployed_contracts.json")
        
        return deployed_contracts
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        raise

if __name__ == "__main__":
    simulate_deployment() 