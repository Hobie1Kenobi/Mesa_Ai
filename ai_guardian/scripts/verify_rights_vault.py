#!/usr/bin/env python3

import os
import json
import requests
import time
from dotenv import load_dotenv

# Load environment variables from parent directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path)

# BaseScan API configuration
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")
BASESCAN_API_URL = "https://api.basescan.org/api"

# Contract details
CONTRACT_ADDRESS = "0xaE77D5307B9055D89b002596B46E8768c3b33c18"
CONTRACT_NAME = "RightsVault"

def verify_contract():
    """Verify the RightsVault contract on BaseScan"""
    print(f"Verifying {CONTRACT_NAME} at {CONTRACT_ADDRESS}...")
    
    # Get the contract source code
    src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", f"{CONTRACT_NAME}.sol")
    
    if not os.path.exists(src_path):
        print(f"❌ Source file not found: {src_path}")
        return False
        
    with open(src_path, "r") as f:
        source_code = f.read()
    
    # Prepare verification data
    verification_data = {
        "apikey": BASESCAN_API_KEY,
        "module": "contract",
        "action": "verifysourcecode",
        "contractaddress": CONTRACT_ADDRESS,
        "sourceCode": source_code,
        "codeformat": "solidity-single-file",
        "contractname": CONTRACT_NAME,
        "compilerversion": "v0.8.19+commit.7dd6d404",
        "optimizationUsed": 1,
        "runs": 200,
        "constructorArguements": "",  # No constructor arguments
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
            print(f"✅ {CONTRACT_NAME} verification submitted successfully!")
            print(f"GUID: {result.get('result')}")
            print(f"Check status at: https://sepolia.basescan.org/address/{CONTRACT_ADDRESS}#code")
            
            # Check verification status
            time.sleep(10)  # Wait for verification to process
            check_verification_status(result.get('result'))
            return True
        else:
            print(f"❌ {CONTRACT_NAME} verification failed: {result.get('message')}")
            if "already verified" in str(result.get('message')).lower():
                print(f"Contract is already verified. You can view it at: https://sepolia.basescan.org/address/{CONTRACT_ADDRESS}#code")
                return True
            return False
            
    except Exception as e:
        print(f"❌ Error submitting verification for {CONTRACT_NAME}: {str(e)}")
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

if __name__ == "__main__":
    if not BASESCAN_API_KEY:
        print("❌ Error: BASESCAN_API_KEY not found in .env file")
        print(f"Looking for .env file at: {dotenv_path}")
        print("Please get your API key from https://basescan.org/apis and add it to your .env file")
        exit(1)
    
    print("=== Contract Verification on BaseScan ===")
    print(f"Using BaseScan API Key: {BASESCAN_API_KEY[:6]}...{BASESCAN_API_KEY[-4:]}")
    
    success = verify_contract()
    if not success:
        print(f"⚠️ Verification failed. You may need to verify manually at:")
        print(f"https://sepolia.basescan.org/address/{CONTRACT_ADDRESS}#code")
    
    print("\n=== Verification Process Complete ===")
    print("Check BaseScan for verification status. It may take a few minutes for verification to complete.")
    print(f"You can check the status at: https://sepolia.basescan.org/address/{CONTRACT_ADDRESS}#code") 