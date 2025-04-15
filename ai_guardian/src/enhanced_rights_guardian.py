#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rights_guardian import RightsGuardian, MusicRight
from web3 import Web3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EnhancedRightsGuardian")

class EnhancedRightsGuardian(RightsGuardian):
    """
    Enhanced version of RightsGuardian that integrates with ERC-6551 and attestations
    """
    
    def __init__(self, web3_provider: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize the enhanced rights guardian
        
        Args:
            web3_provider: Web3 provider URL (default: None, will use localhost:8545)
            config_path: Path to configuration file (default: None)
        """
        super().__init__()
        
        # Initialize Web3 if provider is specified
        self.web3 = None
        if web3_provider:
            self.web3 = Web3(Web3.HTTPProvider(web3_provider))
            logger.info(f"Connected to Web3 provider: {web3_provider}")
        
        # Load configuration
        self.config = {
            "chain_id": 1,
            "contracts": {}
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config.update(json.load(f))
            logger.info(f"Loaded configuration from {config_path}")
        
        # Contract instances
        self.contract_instances = {}
    
    def process_traditional_contract(self, contract_data: Dict) -> Dict:
        """
        Process a traditional contract and extract structured rights information
        
        Args:
            contract_data: Contract data dictionary
            
        Returns:
            Processed contract data dictionary
        """
        logger.info(f"Processing traditional contract: {contract_data.get('title', 'Untitled')}")
        
        # Process with parent class
        music_right = super().process_rights_document(contract_data)
        
        # Add additional metadata for traditional contracts
        traditional_data = {
            'contract_id': contract_data.get('contract_id', f"MESA-{int(datetime.now().timestamp())}"),
            'signers': contract_data.get('signers', []),
            'creation_date': datetime.now().isoformat(),
            'status': 'pending_signatures',
            'rights_data': self.generate_smart_contract_params(music_right)
        }
        
        logger.info(f"Processed traditional contract: {traditional_data['contract_id']}")
        
        return traditional_data
    
    def initialize_web3_contracts(self, registry_address: str, nft_address: str, 
                                 container_impl_address: str, eas_address: str) -> bool:
        """
        Initialize Web3 contract instances
        
        Args:
            registry_address: Address of the ERC6551Registry contract
            nft_address: Address of the MusicRightsNFT contract
            container_impl_address: Address of the MusicRightsContainer implementation contract
            eas_address: Address of the EAS contract
            
        Returns:
            True if successful, False otherwise
        """
        if not self.web3:
            logger.error("Web3 not initialized")
            return False
        
        try:
            # Load contract ABIs
            contracts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            build_dir = os.path.join(contracts_dir, 'build')
            
            # Load ABIs
            with open(os.path.join(build_dir, 'ERC6551Registry.json'), 'r') as f:
                registry_abi = json.load(f)['abi']
            
            with open(os.path.join(build_dir, 'MusicRightsNFT.json'), 'r') as f:
                nft_abi = json.load(f)['abi']
            
            with open(os.path.join(build_dir, 'MusicRightsContainer.json'), 'r') as f:
                container_abi = json.load(f)['abi']
            
            with open(os.path.join(build_dir, 'MockEAS.json'), 'r') as f:
                eas_abi = json.load(f)['abi']
            
            # Create contract instances
            self.contract_instances = {
                'registry': self.web3.eth.contract(address=registry_address, abi=registry_abi),
                'nft': self.web3.eth.contract(address=nft_address, abi=nft_abi),
                'container_impl': self.web3.eth.contract(address=container_impl_address, abi=container_abi),
                'eas': self.web3.eth.contract(address=eas_address, abi=eas_abi)
            }
            
            logger.info("Initialized Web3 contract instances")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Web3 contracts: {str(e)}")
            return False
    
    def register_eas_schema(self) -> str:
        """
        Register the music rights attestation schema
        
        Returns:
            Schema ID as hex string
        """
        if not self.web3 or 'eas' not in self.contract_instances:
            logger.error("Web3 or EAS contract not initialized")
            return ""
        
        try:
            # Default account
            account = self.web3.eth.accounts[0]
            
            schema_name = "MusicRightsSchema"
            schema_description = "Schema for music rights attestations"
            schema_fields = [
                "contractId",
                "artistName",
                "rightsType",
                "percentage",
                "territory",
                "startDate",
                "endDate"
            ]
            
            tx_hash = self.contract_instances['eas'].functions.registerSchema(
                schema_name,
                schema_description,
                schema_fields
            ).transact({'from': account})
            
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get schema ID from event logs
            event = self.contract_instances['eas'].events.SchemaRegistered().process_receipt(tx_receipt)[0]
            schema_id = event['args']['schemaId']
            
            logger.info(f"Registered schema: {schema_id.hex()}")
            
            return schema_id.hex()
            
        except Exception as e:
            logger.error(f"Error registering EAS schema: {str(e)}")
            return ""
    
    def create_attestation(self, schema_id: str, contract_data: Dict, recipient: str) -> str:
        """
        Create an attestation for a music contract
        
        Args:
            schema_id: Schema ID as hex string
            contract_data: Contract data dictionary
            recipient: Recipient address
            
        Returns:
            Attestation ID as hex string
        """
        if not self.web3 or 'eas' not in self.contract_instances:
            logger.error("Web3 or EAS contract not initialized")
            return ""
        
        try:
            # Default account
            account = self.web3.eth.accounts[0]
            
            # Create attestation data - in production, we would properly encode this
            attestation_data = self.web3.to_bytes(text=json.dumps(contract_data))
            
            tx_hash = self.contract_instances['eas'].functions.attest(
                self.web3.to_bytes(hexstr=schema_id),
                recipient,
                attestation_data
            ).transact({'from': account})
            
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get attestation ID from event logs
            event = self.contract_instances['eas'].events.AttestationCreated().process_receipt(tx_receipt)[0]
            attestation_id = event['args']['attestationId']
            
            logger.info(f"Created attestation: {attestation_id.hex()}")
            
            return attestation_id.hex()
            
        except Exception as e:
            logger.error(f"Error creating attestation: {str(e)}")
            return ""
    
    def mint_rights_nft(self, contract_data: Dict, recipient: str) -> int:
        """
        Mint a music rights NFT
        
        Args:
            contract_data: Contract data dictionary
            recipient: Recipient address
            
        Returns:
            Token ID
        """
        if not self.web3 or 'nft' not in self.contract_instances:
            logger.error("Web3 or NFT contract not initialized")
            return 0
        
        try:
            # Default account
            account = self.web3.eth.accounts[0]
            
            tx_hash = self.contract_instances['nft'].functions.mintRights(
                recipient,
                contract_data.get('contractId', ''),
                contract_data.get('rightsType', ''),
                contract_data.get('territory', 'worldwide'),
                f"ipfs://QmHash/{contract_data.get('contractId', '')}"  # Simulated IPFS URI
            ).transact({'from': account})
            
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get token ID from event logs
            event = self.contract_instances['nft'].events.RightsMinted().process_receipt(tx_receipt)[0]
            token_id = event['args']['tokenId']
            
            logger.info(f"Minted NFT with ID: {token_id}")
            
            return token_id
            
        except Exception as e:
            logger.error(f"Error minting rights NFT: {str(e)}")
            return 0
    
    def create_container(self, token_id: int, attestation_id: str, contract_data: Dict) -> str:
        """
        Create a token bound account (container) for the NFT
        
        Args:
            token_id: Token ID
            attestation_id: Attestation ID as hex string
            contract_data: Contract data dictionary
            
        Returns:
            Container address
        """
        if not self.web3 or not all(k in self.contract_instances for k in ['registry', 'nft', 'container_impl']):
            logger.error("Web3 or required contracts not initialized")
            return ""
        
        try:
            # Default account
            account = self.web3.eth.accounts[0]
            
            chain_id = self.config.get('chain_id', 1)
            
            # Create initialization data
            init_data = self.web3.eth.contract(abi=[{
                "inputs": [
                    {"name": "attestationId", "type": "bytes32"},
                    {"name": "contractId", "type": "string"},
                    {"name": "rightsType", "type": "string"},
                    {"name": "territory", "type": "string"}
                ],
                "name": "initialize",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }]).encodeABI(
                fn_name="initialize",
                args=[
                    self.web3.to_bytes(hexstr=attestation_id),
                    contract_data.get('contractId', ''),
                    contract_data.get('rightsType', ''),
                    contract_data.get('territory', 'worldwide')
                ]
            )
            
            # Create the container
            tx_hash = self.contract_instances['registry'].functions.createAccount(
                self.contract_instances['container_impl'].address,
                chain_id,
                self.contract_instances['nft'].address,
                token_id,
                0,  # salt
                init_data
            ).transact({'from': account})
            
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get container address from event logs
            event = self.contract_instances['registry'].events.AccountCreated().process_receipt(tx_receipt)[0]
            container_address = event['args']['account']
            
            logger.info(f"Created container at: {container_address}")
            
            return container_address
            
        except Exception as e:
            logger.error(f"Error creating container: {str(e)}")
            return ""
    
    def create_web3_enhancement(self, contract_data: Dict, recipient: str, schema_id: Optional[str] = None) -> Dict:
        """
        Create a complete Web3 enhancement for a traditional contract
        
        Args:
            contract_data: Contract data dictionary
            recipient: Recipient address (main signer)
            schema_id: Optional schema ID (will register a new one if not provided)
            
        Returns:
            Dictionary with Web3 enhancement data
        """
        try:
            logger.info(f"Creating Web3 enhancement for contract: {contract_data.get('contractId', '')}")
            
            # 1. Register EAS schema if not provided
            if not schema_id:
                schema_id = self.register_eas_schema()
                if not schema_id:
                    raise Exception("Failed to register EAS schema")
            
            # 2. Create attestation
            attestation_id = self.create_attestation(schema_id, contract_data, recipient)
            if not attestation_id:
                raise Exception("Failed to create attestation")
            
            # 3. Mint NFT
            token_id = self.mint_rights_nft(contract_data, recipient)
            if not token_id:
                raise Exception("Failed to mint NFT")
            
            # 4. Create container
            container_address = self.create_container(token_id, attestation_id, contract_data)
            if not container_address:
                raise Exception("Failed to create container")
            
            # 5. Return enhancement data
            enhancement = {
                'schema_id': schema_id,
                'attestation_id': attestation_id,
                'token_id': token_id,
                'container_address': container_address,
                'timestamp': datetime.now().isoformat(),
                'contract_id': contract_data.get('contractId', ''),
                'status': 'active'
            }
            
            logger.info(f"Created Web3 enhancement: {enhancement}")
            
            return enhancement
            
        except Exception as e:
            logger.error(f"Error creating Web3 enhancement: {str(e)}")
            return {
                'error': str(e),
                'status': 'failed',
                'contract_id': contract_data.get('contractId', '')
            }
    
    def process_contract_with_web3(self, contract_data: Dict, recipient: str) -> Dict:
        """
        Complete flow: Process a traditional contract and create Web3 enhancement
        
        Args:
            contract_data: Contract data dictionary
            recipient: Recipient address (main signer)
            
        Returns:
            Dictionary with processed contract and Web3 enhancement data
        """
        # 1. Process traditional contract
        processed_contract = self.process_traditional_contract(contract_data)
        
        # 2. Create Web3 enhancement
        web3_enhancement = self.create_web3_enhancement(processed_contract, recipient)
        
        # 3. Return combined result
        return {
            'traditional_contract': processed_contract,
            'web3_enhancement': web3_enhancement
        }
    
    def configure_payment_splitting(self, container_address: str, recipients: List[str], shares: List[int]) -> bool:
        """
        Configure payment splitting for a container
        
        Args:
            container_address: Container address
            recipients: List of recipient addresses
            shares: List of shares for each recipient
            
        Returns:
            True if successful, False otherwise
        """
        if not self.web3:
            logger.error("Web3 not initialized")
            return False
        
        try:
            # Default account
            account = self.web3.eth.accounts[0]
            
            # Create container contract instance
            container = self.web3.eth.contract(
                address=container_address,
                abi=self.contract_instances['container_impl'].abi
            )
            
            # Configure payment splitting
            tx_hash = container.functions.configurePaymentSplitting(
                recipients,
                shares
            ).transact({'from': account})
            
            self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Configured payment splitting for container: {container_address}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error configuring payment splitting: {str(e)}")
            return False
    
    def add_rights_holder_wallet(self, container_address: str, email: str, wallet: str) -> bool:
        """
        Add a rights holder wallet to a container
        
        Args:
            container_address: Container address
            email: Email address of the rights holder
            wallet: Wallet address of the rights holder
            
        Returns:
            True if successful, False otherwise
        """
        if not self.web3:
            logger.error("Web3 not initialized")
            return False
        
        try:
            # Default account
            account = self.web3.eth.accounts[0]
            
            # Create container contract instance
            container = self.web3.eth.contract(
                address=container_address,
                abi=self.contract_instances['container_impl'].abi
            )
            
            # Add rights holder wallet
            tx_hash = container.functions.addRightsHolderWallet(
                email,
                wallet
            ).transact({'from': account})
            
            self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Added rights holder wallet for {email}: {wallet}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding rights holder wallet: {str(e)}")
            return False

def main():
    """Test the enhanced rights guardian"""
    # Initialize the guardian
    guardian = EnhancedRightsGuardian()
    
    # Example contract data
    contract_data = {
        'title': 'Summer Nights',
        'artist': 'John Doe',
        'rights_holder': '0x1234567890123456789012345678901234567890',
        'rights_type': 'master_recording',
        'percentage': 75,  # 75%
        'territory': 'global',
        'signers': [
            {'email': 'artist@example.com', 'role': 'artist'},
            {'email': 'producer@example.com', 'role': 'producer'},
            {'email': 'publisher@example.com', 'role': 'publisher'}
        ]
    }
    
    # Process traditional contract
    processed_contract = guardian.process_traditional_contract(contract_data)
    print(json.dumps(processed_contract, indent=2))
    
    # Note: In a real scenario, we would initialize the web3 contracts and
    # create the Web3 enhancement after all parties have signed the traditional contract
    
if __name__ == "__main__":
    main() 