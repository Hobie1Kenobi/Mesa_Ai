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

def check_contract_status():
    """Check the status of the contract on BaseScan"""
    print(f"Checking contract status at {CONTRACT_ADDRESS}...")
    
    # Check if the contract exists
    balance_data = {
        "apikey": BASESCAN_API_KEY,
        "module": "account",
        "action": "balance",
        "address": CONTRACT_ADDRESS,
        "tag": "latest"
    }
    
    try:
        print("Checking contract balance...")
        response = requests.get(BASESCAN_API_URL, params=balance_data)
        response.raise_for_status()
        
        result = response.json()
        print(f"Balance response: {result}")
        
        if result.get("status") == "1":
            print(f"✅ Contract exists on BaseScan with balance: {result.get('result')}")
        else:
            print(f"❌ Contract not found on BaseScan: {result.get('message')}")
            return False
    
    except Exception as e:
        print(f"❌ Error checking contract balance: {str(e)}")
        return False
    
    # Check if the contract is verified
    abi_data = {
        "apikey": BASESCAN_API_KEY,
        "module": "contract",
        "action": "getabi",
        "address": CONTRACT_ADDRESS
    }
    
    try:
        print("\nChecking if contract is verified...")
        response = requests.get(BASESCAN_API_URL, params=abi_data)
        response.raise_for_status()
        
        result = response.json()
        print(f"ABI response: {result}")
        
        if result.get("status") == "1":
            print(f"✅ Contract is verified on BaseScan!")
            return True
        else:
            print(f"❌ Contract is not verified on BaseScan: {result.get('message')}")
            return False
    
    except Exception as e:
        print(f"❌ Error checking contract ABI: {str(e)}")
        return False

if __name__ == "__main__":
    if not BASESCAN_API_KEY:
        print("❌ Error: BASESCAN_API_KEY not found in .env file")
        print(f"Looking for .env file at: {dotenv_path}")
        print("Please get your API key from https://basescan.org/apis and add it to your .env file")
        exit(1)
    
    print("=== Contract Status Check on BaseScan ===")
    print(f"Using BaseScan API Key: {BASESCAN_API_KEY[:6]}...{BASESCAN_API_KEY[-4:]}")
    
    exists = check_contract_status()
    if exists:
        print(f"\n✅ Contract exists and is verified on BaseScan!")
        print(f"You can view it at: https://sepolia.basescan.org/address/{CONTRACT_ADDRESS}#code")
    else:
        print(f"\n⚠️ Contract exists but is not verified on BaseScan.")
        print(f"You can verify it manually at: https://sepolia.basescan.org/address/{CONTRACT_ADDRESS}#code")
    
    print("\n=== Status Check Complete ===") 