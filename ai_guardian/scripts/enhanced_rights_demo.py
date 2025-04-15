#!/usr/bin/env python3

import sys
import os
import json
from datetime import datetime, timedelta
import time
import logging
import argparse

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EnhancedRightsDemo")

def simulate_traditional_contract_creation(contract_data):
    """Simulate creating a traditional contract"""
    logger.info(f"Creating traditional contract for: {contract_data['title']}")
    
    # Add some metadata
    contract_data['contract_id'] = f"MESA-{int(time.time())}"
    contract_data['creation_date'] = datetime.now().isoformat()
    
    return contract_data

def simulate_email_signatures(contract_data):
    """Simulate the email/SMS signature process"""
    logger.info(f"Sending signature requests for contract: {contract_data['contract_id']}")
    
    # Log details
    print("\n=== Signature Requests ===")
    for signer in contract_data.get('signers', []):
        print(f"✉️  Sent to: {signer['email']} ({signer['role']})")
    
    # Simulate waiting for signatures
    print("\n⏳ Waiting for signatures...")
    time.sleep(2)  # simulate delay
    
    # Simulate all parties signing
    print("\n=== Signatures Received ===")
    for signer in contract_data.get('signers', []):
        print(f"✅ Signed by: {signer['email']} ({signer['role']})")
    
    contract_data['status'] = 'signed'
    contract_data['signed_date'] = datetime.now().isoformat()
    
    return contract_data

def deploy_mock_contracts():
    """
    This would actually deploy the contracts, but for demo purposes
    we'll just simulate it with fixed addresses
    """
    logger.info("Deploying mock contracts for demo")
    
    # Simulate contract deployment
    print("\n=== Deploying Contracts ===")
    time.sleep(1)
    print("✅ ERC6551Registry deployed")
    time.sleep(0.5)
    print("✅ MusicRightsNFT deployed")
    time.sleep(0.5)
    print("✅ MusicRightsContainer implementation deployed")
    time.sleep(0.5)
    print("✅ MockEAS deployed")
    
    # Mock contract addresses
    return {
        'registry': '0x123456789012345678901234567890REGISTRY',
        'nft': '0x123456789012345678901234567890NFT12345',
        'container_impl': '0x123456789012345678901234567890CONTAINER',
        'eas': '0x123456789012345678901234567890EAS12345'
    }

def simulate_web3_enhancement(contract_data, signer_addresses):
    """Simulate the Web3 enhancement process"""
    logger.info(f"Creating Web3 enhancement for contract: {contract_data['contract_id']}")
    
    # Main signer (artist) address
    main_signer = signer_addresses[0]
    
    # Mock schema creation and attestation
    print("\n=== Creating Web3 Enhancement ===")
    time.sleep(1)
    schema_id = f"0x{os.urandom(32).hex()}"
    print(f"✅ Schema registered: {schema_id[:10]}...{schema_id[-8:]}")
    
    time.sleep(1)
    attestation_id = f"0x{os.urandom(32).hex()}"
    print(f"✅ Attestation created: {attestation_id[:10]}...{attestation_id[-8:]}")
    
    time.sleep(1)
    token_id = 1
    print(f"✅ Rights NFT minted: Token ID {token_id}")
    
    time.sleep(1)
    container_address = f"0x{os.urandom(20).hex()}"
    print(f"✅ Container created: {container_address}")
    
    # Simulate payment splitting setup
    time.sleep(1)
    print("\n=== Configuring Payment Splitting ===")
    for i, signer in enumerate(contract_data.get('signers', [])):
        print(f"👛 Added {signer['role']}: {signer_addresses[i]}")
    
    # Create enhancement data
    enhancement = {
        'schema_id': schema_id,
        'attestation_id': attestation_id,
        'token_id': token_id,
        'container_address': container_address,
        'timestamp': datetime.now().isoformat(),
        'contract_id': contract_data['contract_id'],
        'status': 'active',
        'payment_splitting': {
            'configured': True,
            'recipients': signer_addresses,
            'roles': [signer['role'] for signer in contract_data.get('signers', [])],
            'shares': [70, 20, 10]  # 70% artist, 20% producer, 10% publisher
        }
    }
    
    return enhancement

def simulate_payment_distribution(enhancement):
    """Simulate a royalty payment distribution"""
    logger.info(f"Simulating payment distribution for container: {enhancement['container_address']}")
    
    print("\n=== Royalty Payment Distribution ===")
    print(f"💰 Payment received: 1.0 ETH")
    time.sleep(1)
    
    # Get payment data from enhancement
    recipients = enhancement['payment_splitting']['recipients']
    roles = enhancement['payment_splitting']['roles']
    shares = enhancement['payment_splitting']['shares']
    
    # Calculate amounts
    total_eth = 1.0
    amounts = [(share / 100) * total_eth for share in shares]
    
    # Show distribution
    print("\n📊 Payment Distribution:")
    for i in range(len(recipients)):
        print(f"  • {roles[i]}: {amounts[i]:.2f} ETH ({shares[i]}%) → {recipients[i]}")
    
    time.sleep(1)
    print("\n✅ All payments distributed successfully!")
    
    return {
        'total_amount': total_eth,
        'timestamp': datetime.now().isoformat(),
        'distributions': [
            {'role': roles[i], 'amount': amounts[i], 'recipient': recipients[i], 'share': shares[i]}
            for i in range(len(recipients))
        ]
    }

def run_demo():
    """Run the full demo flow"""
    print("\n" + "=" * 80)
    print("🎵  MESA RIGHTS VAULT ENHANCED DEMO 🎵")
    print("=" * 80)
    
    # 1. Define example contract data
    contract_data = {
        'title': 'Summer Nights',
        'artist': 'John Doe',
        'rights_holder': '0x1234567890123456789012345678901234567890',
        'rights_type': 'master_recording',
        'percentage': 75,  # 75%
        'territory': 'worldwide',
        'signers': [
            {'email': 'artist@example.com', 'role': 'artist'},
            {'email': 'producer@example.com', 'role': 'producer'},
            {'email': 'publisher@example.com', 'role': 'publisher'}
        ]
    }
    
    # 2. Simulate the traditional contract flow
    print("\n📝 TRADITIONAL CONTRACT FLOW")
    print("-" * 80)
    
    contract_data = simulate_traditional_contract_creation(contract_data)
    contract_data = simulate_email_signatures(contract_data)
    
    # 3. Simulate mock contracts deployment
    mock_contracts = deploy_mock_contracts()
    
    # 4. Simulate wallet addresses for signers
    signer_addresses = [
        '0x1111111111111111111111111111111111111111',  # Artist
        '0x2222222222222222222222222222222222222222',  # Producer
        '0x3333333333333333333333333333333333333333'   # Publisher
    ]
    
    # 5. Simulate Web3 enhancement
    print("\n🌐 WEB3 ENHANCEMENT LAYER")
    print("-" * 80)
    enhancement = simulate_web3_enhancement(contract_data, signer_addresses)
    
    # 6. Simulate a payment distribution
    print("\n💸 PAYMENT SIMULATION")
    print("-" * 80)
    payment = simulate_payment_distribution(enhancement)
    
    # 7. Display summary
    print("\n📋 SUMMARY")
    print("-" * 80)
    print(f"• Traditional Contract: {contract_data['contract_id']}")
    print(f"• Contract Status: {contract_data['status']}")
    print(f"• Created: {contract_data['creation_date']}")
    print(f"• Signed: {contract_data['signed_date']}")
    print(f"• Web3 Container: {enhancement['container_address']}")
    print(f"• NFT ID: {enhancement['token_id']}")
    print(f"• Payment Enabled: {'Yes' if enhancement['payment_splitting']['configured'] else 'No'}")
    
    # 8. Save demo results to file
    results = {
        'traditional_contract': contract_data,
        'web3_enhancement': enhancement,
        'payment_simulation': payment,
        'timestamp': datetime.now().isoformat()
    }
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"demo_result_{int(time.time())}.json")
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Demo results saved to: {output_file}")
    print("\n" + "=" * 80)
    print("🎵  DEMO COMPLETED SUCCESSFULLY 🎵")
    print("=" * 80)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Enhanced Rights Vault Demo')
    parser.add_argument('--save-only', action='store_true', help='Save demo results without simulating')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    run_demo()