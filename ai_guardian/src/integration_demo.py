from rights_guardian import RightsGuardian
from web3 import Web3
import json
from datetime import datetime, timedelta

def main():
    # Initialize the Rights Guardian AI
    guardian = RightsGuardian()
    
    # Example rights document
    rights_doc = {
        "title": "Summer Nights",
        "artist": "John Doe",
        "rights_holder": "0x1234567890123456789012345678901234567890",
        "rights_type": "composition",
        "percentage": 0.75,  # 75%
        "territory": "global",
        "start_date": datetime.now().isoformat(),
        "end_date": (datetime.now() + timedelta(years=5)).isoformat(),
        "metadata": {
            "iswc": "T-123.456.789-0",
            "genre": "pop",
            "language": "english"
        }
    }
    
    # Process the rights document
    print("Processing rights document...")
    right = guardian.process_rights_document(rights_doc)
    print(f"Processed right ID: {guardian._generate_right_id(right)}")
    
    # Generate smart contract parameters
    print("\nGenerating smart contract parameters...")
    contract_params = guardian.generate_smart_contract_params(right)
    print(json.dumps(contract_params, indent=2))
    
    # Generate privacy-preserving proof
    print("\nGenerating privacy-preserving proof...")
    proof = guardian.generate_privacy_proof(right, reveal_fields=["rights_holder", "percentage"])
    print(json.dumps(proof, indent=2))
    
    # Simulate smart contract interaction
    print("\nSimulating smart contract interaction...")
    print("To register this right on the blockchain, you would call:")
    print(f"""
    contract.registerRight(
        "{contract_params['rightId']}",
        "{contract_params['rightsType']}",
        {contract_params['percentage']},
        "{contract_params['territory']}",
        "{contract_params['startDate']}",
        "{contract_params['endDate']}",
        "{contract_params['metadataHash']}"
    )
    """)
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    main() 