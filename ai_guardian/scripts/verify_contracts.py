#!/usr/bin/env python3

import os
import json
import requests
import time
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables from parent directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path)

# BaseScan API configuration
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")
BASESCAN_API_URL = "https://api.basescan.org/api"

# Contract addresses from deployment (Updated YYYY-MM-DD)
CONTRACT_ADDRESSES = {
    "RightsVault": "0xC2aC41FBB401B5620133Ff94606F758DbF750517",
    "MusicRightsVault": "0xD08BC592446e6cb5A85D5c9e84b928Fa55dDF315",
    "VerificationRegistry": "0x8c9f21191F29Ad6f6479134E1b9dA0907c3A1Ed5",
    "EnhancedVerification": "0x1C8c381f6135aA58e86E71c653900e3F95968a4f",
    "UsageTracker": "0x467a7F977b5D0cc22aC3dF56b138228DA77F36B3",
    "RoyaltyManager": "0xf76d44e87cd3EC26e8018Fd5aE1722A70D17d8b0"
}

# Constructor arguments for contracts that need them
CONSTRUCTOR_ARGS = {
    "RightsVault": None,  # No constructor arguments
    "MusicRightsVault": CONTRACT_ADDRESSES["RightsVault"],  # RightsVault address
    "VerificationRegistry": None,  # No constructor arguments
    "EnhancedVerification": CONTRACT_ADDRESSES["RightsVault"],  # RightsVault address
    "UsageTracker": CONTRACT_ADDRESSES["RightsVault"],  # RightsVault address
    "RoyaltyManager": CONTRACT_ADDRESSES["RightsVault"],  # RightsVault address
}

def encode_constructor_args(contract_name):
    """Encode constructor arguments for verification"""
    args = CONSTRUCTOR_ARGS.get(contract_name)
    
    if args is None:
        return ""
    
    # For simple address arguments
    if isinstance(args, str) and args.startswith("0x"):
        # Remove 0x prefix and pad to 32 bytes
        return args[2:].lower().zfill(64)
    
    # For more complex arguments, you would need to handle them specifically
    return ""

def verify_contract(contract_name, contract_address):
    """Verify a contract on BaseScan"""
    print(f"Verifying {contract_name} at {contract_address}...")
    
    # Get the contract source code
    src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", f"{contract_name}.sol")
    
    if not os.path.exists(src_path):
        print(f"❌ Source file not found: {src_path}")
        return False
        
    with open(src_path, "r") as f:
        source_code = f.read()
    
    # Get constructor arguments
    constructor_args = encode_constructor_args(contract_name)
    constructor_args_str = f"Constructor arguments: {constructor_args}" if constructor_args else "No constructor arguments"
    print(constructor_args_str)
    
    # Prepare verification data
    verification_data = {
        "apikey": BASESCAN_API_KEY,
        "module": "contract",
        "action": "verifysourcecode",
        "contractaddress": contract_address,
        "sourceCode": source_code,
        "codeformat": "solidity-single-file",
        "contractname": contract_name,
        "compilerversion": "v0.8.19+commit.7dd6d404",
        "optimizationUsed": 1,
        "runs": 200,
        "constructorArguments": constructor_args,
        "evmversion": "london",
        "licenseType": 3  # MIT License
    }
    
    # Send verification request
    try:
        print("Sending verification request...")
        response = requests.post(BASESCAN_API_URL, data=verification_data)
        response.raise_for_status()
        
        result = response.json()
        print(f"Response: {result}")
        
        if result.get("status") == "1":
            print(f"✅ {contract_name} verification submitted successfully!")
            print(f"GUID: {result.get('result')}")
            print(f"Check status at: https://sepolia.basescan.org/address/{contract_address}#code")
            
            # Check verification status
            time.sleep(10)  # Wait for verification to process
            check_verification_status(result.get('result'))
            return True
        else:
            print(f"❌ {contract_name} verification failed: {result.get('message')}")
            if "already verified" in str(result.get('message')).lower():
                print(f"Contract is already verified. You can view it at: https://sepolia.basescan.org/address/{contract_address}#code")
                return True
            return False
            
    except Exception as e:
        print(f"❌ Error submitting verification for {contract_name}: {str(e)}")
        return False

def check_verification_status(guid):
    """Check the status of a verification request"""
    check_data = {
        "apikey": BASESCAN_API_KEY,
        "module": "contract",
        "action": "checkverifystatus",
        "guid": guid
    }
    
    try:
        response = requests.get(BASESCAN_API_URL, params=check_data)
        result = response.json()
        
        if result.get("status") == "1":
            print("✅ Verification completed successfully!")
        else:
            print(f"⚠️ Verification status: {result.get('result')}")
            
    except Exception as e:
        print(f"❌ Error checking verification status: {str(e)}")

def main():
    """Verify all contracts"""
    if not BASESCAN_API_KEY:
        print("❌ Error: BASESCAN_API_KEY not found in .env file")
        print(f"Looking for .env file at: {dotenv_path}")
        print("Please get your API key from https://basescan.org/apis and add it to your .env file")
        return
    
    print("=== Contract Verification on BaseScan ===")
    print(f"Using BaseScan API Key: {BASESCAN_API_KEY[:6]}...{BASESCAN_API_KEY[-4:]}")
    
    for contract_name, contract_address in CONTRACT_ADDRESSES.items():
        success = verify_contract(contract_name, contract_address)
        if not success:
            print(f"⚠️ Verification for {contract_name} failed. You may need to verify manually at:")
            print(f"https://sepolia.basescan.org/address/{contract_address}#code")
        
        # Wait a bit between verifications to avoid rate limiting
        time.sleep(5)
    
    print("\n=== Verification Process Complete ===")
    print("Check BaseScan for verification status. It may take a few minutes for verification to complete.")
    print("You can check the status at: https://sepolia.basescan.org/address/")

if __name__ == "__main__":
    main() 