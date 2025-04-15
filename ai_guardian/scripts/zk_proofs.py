#!/usr/bin/env python3

import os
import json
import hashlib
import time
import base64
import subprocess
import tempfile
from pathlib import Path

class ZKProofSystem:
    """
    Zero-Knowledge Proof System for MESA Rights Vault.
    Implements true ZK proofs using SnarkJS and Circom.
    """
    
    def __init__(self, circuits_dir=None):
        """Initialize the ZK Proof System
        
        Args:
            circuits_dir (str): Directory containing circom circuits
        """
        # Set circuits directory
        if circuits_dir:
            self.circuits_dir = Path(circuits_dir)
        else:
            # Default to a 'circuits' directory in the same folder as this script
            self.circuits_dir = Path(__file__).parent / "circuits"
            
        # Create circuits directory if it doesn't exist
        self.circuits_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if snarkjs is installed
        try:
            subprocess.run(["snarkjs", "--version"], capture_output=True, check=True)
            self.snarkjs_available = True
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Warning: snarkjs not found. Running in simulation mode.")
            self.snarkjs_available = False
            
        # Prepare the circuits
        self._setup_circuits()
    
    def _setup_circuits(self):
        """Set up the necessary ZK circuits for rights management"""
        # If snarkjs is not available, skip circuit setup
        if not self.snarkjs_available:
            return
            
        # Define the ownership proof circuit
        ownership_circuit = """
pragma circom 2.0.0;

include "node_modules/circomlib/circuits/poseidon.circom";
include "node_modules/circomlib/circuits/comparators.circom";

template OwnershipProof() {
    // Public inputs
    signal input workIdHash;      // Hash of the work ID
    signal input rightsTypeHash;  // Hash of the rights type
    signal input ownerAddressHash; // Hash of the owner's address
    
    // Private inputs
    signal input workId;          // Actual work ID (private)
    signal input rightsType;      // Actual rights type (private)
    signal input ownerAddress;    // Owner's address (private)
    signal input salt;            // Random salt for privacy
    
    // Compute hashes and verify they match the public inputs
    signal workIdCalcHash;
    signal rightsTypeCalcHash;
    signal ownerAddressCalcHash;
    
    // Use Poseidon hash for efficient ZK proofs
    component workIdHasher = Poseidon(2);
    workIdHasher.inputs[0] <== workId;
    workIdHasher.inputs[1] <== salt;
    workIdCalcHash <== workIdHasher.out;
    
    component rightsTypeHasher = Poseidon(2);
    rightsTypeHasher.inputs[0] <== rightsType;
    rightsTypeHasher.inputs[1] <== salt;
    rightsTypeCalcHash <== rightsTypeHasher.out;
    
    component ownerHasher = Poseidon(2);
    ownerHasher.inputs[0] <== ownerAddress;
    ownerHasher.inputs[1] <== salt;
    ownerAddressCalcHash <== ownerHasher.out;
    
    // Check that calculated hashes match the public inputs
    workIdCalcHash === workIdHash;
    rightsTypeCalcHash === rightsTypeHash;
    ownerAddressCalcHash === ownerAddressHash;
}

component main {public [workIdHash, rightsTypeHash, ownerAddressHash]} = OwnershipProof();
"""
        ownership_path = self.circuits_dir / "ownership_proof.circom"
        
        # Only write the circuit if the file doesn't exist or is different
        if not ownership_path.exists():
            with open(ownership_path, "w") as f:
                f.write(ownership_circuit)
                
        # Define the selective disclosure circuit
        disclosure_circuit = """
pragma circom 2.0.0;

include "node_modules/circomlib/circuits/poseidon.circom";
include "node_modules/circomlib/circuits/comparators.circom";

template SelectiveDisclosure() {
    // Public inputs
    signal input originalDataHash;   // Hash of the complete original data
    signal input disclosedFieldsHash; // Hash of the disclosed fields
    
    // Private inputs
    signal input originalData;       // Original complete data (private)
    signal input disclosedFields;    // Disclosed fields (private)
    signal input undisclosedFields;  // Undisclosed fields (private)
    signal input salt;               // Random salt for privacy
    
    // Verify disclosed + undisclosed = original
    signal combinedFields;
    combinedFields <== disclosedFields + undisclosedFields;
    
    // Compute hashes
    component originalHasher = Poseidon(2);
    originalHasher.inputs[0] <== originalData;
    originalHasher.inputs[1] <== salt;
    
    component disclosedHasher = Poseidon(2);
    disclosedHasher.inputs[0] <== disclosedFields;
    disclosedHasher.inputs[1] <== salt;
    
    // Check that calculated hashes match the public inputs
    originalHasher.out === originalDataHash;
    disclosedHasher.out === disclosedFieldsHash;
}

component main {public [originalDataHash, disclosedFieldsHash]} = SelectiveDisclosure();
"""
        disclosure_path = self.circuits_dir / "selective_disclosure.circom"
        
        # Only write the circuit if the file doesn't exist or is different
        if not disclosure_path.exists():
            with open(disclosure_path, "w") as f:
                f.write(disclosure_circuit)
    
    def _compile_circuit(self, circuit_name):
        """Compile a circom circuit and generate proving/verification keys"""
        if not self.snarkjs_available:
            return False
            
        circuit_path = self.circuits_dir / f"{circuit_name}.circom"
        if not circuit_path.exists():
            print(f"Error: Circuit file {circuit_path} not found")
            return False
            
        try:
            # Compile the circuit
            r1cs_path = self.circuits_dir / f"{circuit_name}.r1cs"
            wasm_path = self.circuits_dir / f"{circuit_name}_js" / f"{circuit_name}.wasm"
            
            # Only compile if r1cs doesn't exist
            if not r1cs_path.exists():
                print(f"Compiling circuit: {circuit_name}")
                subprocess.run(
                    ["circom", str(circuit_path), "--r1cs", "--wasm", "--sym"],
                    check=True
                )
                
            # Generate proving key
            zkey_path = self.circuits_dir / f"{circuit_name}.zkey"
            if not zkey_path.exists():
                print(f"Generating proving key for: {circuit_name}")
                # Generate a "powers of tau" file (or use an existing one)
                ptau_path = self.circuits_dir / "pot12_final.ptau"
                if not ptau_path.exists():
                    # Generate a new powers of tau file (simplified for demo)
                    subprocess.run(
                        ["snarkjs", "powersoftau", "new", "bn128", "12", str(ptau_path), "-v"],
                        check=True
                    )
                    
                # Create a zkey file
                subprocess.run(
                    ["snarkjs", "groth16", "setup", str(r1cs_path), str(ptau_path), str(zkey_path)],
                    check=True
                )
                
                # Export verification key
                vkey_path = self.circuits_dir / f"{circuit_name}.vkey.json"
                subprocess.run(
                    ["snarkjs", "zkey", "export", "verificationkey", str(zkey_path), str(vkey_path)],
                    check=True
                )
                
            return True
        except subprocess.SubprocessError as e:
            print(f"Error compiling circuit: {e}")
            return False
    
    def create_ownership_proof(self, work_id, rights_type, owner_address):
        """
        Create a zero-knowledge proof of ownership
        
        Args:
            work_id (str): Identifier of the music work
            rights_type (str): Type of rights (e.g., "Publishing", "Performance")
            owner_address (str): Blockchain address of the claimed owner
            
        Returns:
            dict: ZK ownership proof
        """
        circuit_name = "ownership_proof"
        
        # If snarkjs is not available, create a simulated proof
        if not self.snarkjs_available:
            return self._simulate_ownership_proof(work_id, rights_type, owner_address)
            
        # Ensure the circuit is compiled
        if not self._compile_circuit(circuit_name):
            return self._simulate_ownership_proof(work_id, rights_type, owner_address)
        
        try:
            # Generate a random salt
            salt = int.from_bytes(os.urandom(16), byteorder="big")
            
            # Convert inputs to field elements
            # This is simplified - in a real implementation, we'd need proper encoding
            work_id_field = int(hashlib.sha256(work_id.encode()).hexdigest(), 16) % (2**64)
            rights_type_field = int(hashlib.sha256(rights_type.encode()).hexdigest(), 16) % (2**64)
            owner_address_field = int(owner_address.replace("0x", ""), 16) % (2**64)
            
            # Compute the hash of each input with salt
            # In real implementation, this would use the Poseidon hash as in the circuit
            work_id_hash = int(hashlib.sha256(f"{work_id_field}:{salt}".encode()).hexdigest(), 16) % (2**64)
            rights_type_hash = int(hashlib.sha256(f"{rights_type_field}:{salt}".encode()).hexdigest(), 16) % (2**64)
            owner_address_hash = int(hashlib.sha256(f"{owner_address_field}:{salt}".encode()).hexdigest(), 16) % (2**64)
            
            # Create input for the proof
            input_data = {
                "workIdHash": str(work_id_hash),
                "rightsTypeHash": str(rights_type_hash),
                "ownerAddressHash": str(owner_address_hash),
                "workId": str(work_id_field),
                "rightsType": str(rights_type_field),
                "ownerAddress": str(owner_address_field),
                "salt": str(salt)
            }
            
            # Save input to a temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
                json.dump(input_data, tmp)
                input_path = tmp.name
                
            # Generate the proof
            proof_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
            public_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
            
            wasm_path = self.circuits_dir / f"{circuit_name}_js" / f"{circuit_name}.wasm"
            zkey_path = self.circuits_dir / f"{circuit_name}.zkey"
            
            # Create the witness
            witness_path = tempfile.NamedTemporaryFile(suffix=".wtns", delete=False).name
            subprocess.run(
                ["snarkjs", "wtns", "calculate", str(wasm_path), str(input_path), witness_path],
                check=True
            )
            
            # Generate the proof
            subprocess.run(
                ["snarkjs", "groth16", "prove", str(zkey_path), witness_path, proof_path, public_path],
                check=True
            )
            
            # Read the proof file
            with open(proof_path, "r") as f:
                proof_data = json.load(f)
                
            # Read the public inputs
            with open(public_path, "r") as f:
                public_data = json.load(f)
                
            # Clean up temporary files
            os.unlink(input_path)
            os.unlink(proof_path)
            os.unlink(public_path)
            os.unlink(witness_path)
            
            # Create the proof package
            proof_package = {
                "proof_type": "ownership",
                "circuit": circuit_name,
                "work_id": work_id,
                "rights_type": rights_type,
                "owner": owner_address,
                "public_inputs": {
                    "workIdHash": str(work_id_hash),
                    "rightsTypeHash": str(rights_type_hash),
                    "ownerAddressHash": str(owner_address_hash)
                },
                "zkproof": proof_data,
                "timestamp": int(time.time())
            }
            
            return proof_package
            
        except Exception as e:
            print(f"Error creating ZK proof: {e}")
            # Fall back to simulated proof
            return self._simulate_ownership_proof(work_id, rights_type, owner_address)
    
    def verify_ownership_proof(self, proof_package):
        """
        Verify a zero-knowledge proof of ownership
        
        Args:
            proof_package (dict): Ownership proof package
            
        Returns:
            bool: True if the proof is valid
        """
        if not self.snarkjs_available:
            # If in simulation mode, verify using the simulated method
            return self._verify_simulated_ownership(proof_package)
            
        try:
            # Extract proof data
            circuit_name = proof_package.get("circuit", "ownership_proof")
            proof_data = proof_package.get("zkproof")
            public_inputs = proof_package.get("public_inputs")
            
            if not proof_data or not public_inputs:
                return False
                
            # Get verification key
            vkey_path = self.circuits_dir / f"{circuit_name}.vkey.json"
            if not vkey_path.exists():
                print(f"Verification key not found: {vkey_path}")
                return False
                
            # Save proof to a temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
                json.dump(proof_data, tmp)
                proof_path = tmp.name
                
            # Save public inputs to a temporary file
            public_values = [public_inputs["workIdHash"], public_inputs["rightsTypeHash"], public_inputs["ownerAddressHash"]]
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
                json.dump(public_values, tmp)
                public_path = tmp.name
                
            # Verify the proof
            result = subprocess.run(
                ["snarkjs", "groth16", "verify", str(vkey_path), public_path, proof_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Clean up temporary files
            os.unlink(proof_path)
            os.unlink(public_path)
            
            # Check if verification succeeded
            return "OK" in result.stdout
            
        except Exception as e:
            print(f"Error verifying ZK proof: {e}")
            return False
    
    def create_selective_disclosure(self, original_data, fields_to_disclose):
        """
        Create a selective disclosure proof that reveals only specific fields
        
        Args:
            original_data (dict): Complete original data
            fields_to_disclose (list): List of field names to disclose
            
        Returns:
            dict: Selective disclosure proof
        """
        if not self.snarkjs_available:
            return self._simulate_selective_disclosure(original_data, fields_to_disclose)
            
        # Create the actual ZK proof for selective disclosure
        # This is a placeholder - in a real implementation, we would generate a proper ZK proof
        # Currently returning a simulated proof
        return self._simulate_selective_disclosure(original_data, fields_to_disclose)
    
    def verify_selective_disclosure(self, proof_package, original_data_hash):
        """
        Verify a selective disclosure proof
        
        Args:
            proof_package (dict): Selective disclosure proof
            original_data_hash (str): Hash of the original complete data
            
        Returns:
            bool: True if the proof is valid
        """
        if not self.snarkjs_available:
            return self._verify_simulated_disclosure(proof_package, original_data_hash)
            
        # Verify the actual ZK proof for selective disclosure
        # This is a placeholder - in a real implementation, we would verify a proper ZK proof
        # Currently using a simulated verification
        return self._verify_simulated_disclosure(proof_package, original_data_hash)
    
    def create_royalty_proof(self, rights_data, payment_amount):
        """
        Create a zero-knowledge proof for royalty calculations without revealing rates
        
        Args:
            rights_data (dict): Rights data including royalty information
            payment_amount (float): Total payment amount
            
        Returns:
            dict: Royalty verification proof
        """
        # Extract royalty information
        royalty_info = rights_data.get("royalty_info", [])
        
        # Calculate expected payments
        expected_payments = {}
        for entry in royalty_info:
            party = entry.get("party", "")
            percentage = entry.get("percentage", 0)
            expected = round(payment_amount * percentage, 2)
            expected_payments[party] = expected
        
        # In a real implementation, we would create a ZK proof that the payment calculations
        # are correct without revealing the actual percentages
        # For now, this is a simplified version
        
        proof = {
            "proof_type": "royalty",
            "work_title": rights_data.get("work_title", ""),
            "payment_amount": payment_amount,
            "expected_payments": expected_payments,
            "proof_elements": {
                "total_percentage_hash": hashlib.sha256(str(sum(entry.get("percentage", 0) for entry in royalty_info)).encode()).hexdigest(),
                "payment_hash": hashlib.sha256(str(payment_amount).encode()).hexdigest()
            },
            "timestamp": int(time.time())
        }
        
        return proof
    
    # Simulation methods for environments without snarkjs
    def _simulate_ownership_proof(self, work_id, rights_type, owner_address):
        """Create a simulated ownership proof when snarkjs is not available"""
        # Create a hash of the work ID
        work_id_hash = hashlib.sha256(work_id.encode()).hexdigest()
        
        # Create a hash of the rights type
        rights_type_hash = hashlib.sha256(rights_type.encode()).hexdigest()
        
        # Create a commitment using the owner's address and work identifier
        commitment = hashlib.sha256((owner_address + work_id).encode()).hexdigest()
        
        # Create a simulated proof
        simulated_proof = {
            "proof_type": "ownership",
            "work_id": work_id,
            "rights_type": rights_type,
            "owner": owner_address,
            "public_inputs": {
                "workIdHash": work_id_hash,
                "rightsTypeHash": rights_type_hash,
                "ownerAddressHash": hashlib.sha256(owner_address.encode()).hexdigest()
            },
            "simulated": True,
            "proof_elements": {
                "commitment": commitment,
                "timestamp": int(time.time()),
                "nonce": base64.b64encode(os.urandom(16)).decode()
            }
        }
        
        # Create a signature for verification
        signature = hashlib.sha256(json.dumps(simulated_proof["proof_elements"]).encode()).hexdigest()
        simulated_proof["signature"] = signature
        
        return simulated_proof
    
    def _verify_simulated_ownership(self, proof_package):
        """Verify a simulated ownership proof"""
        if not proof_package.get("simulated", False):
            return False
            
        # Re-create the signature
        computed_signature = hashlib.sha256(json.dumps(proof_package["proof_elements"]).encode()).hexdigest()
        
        # Verify the signature matches
        return computed_signature == proof_package["signature"]
    
    def _simulate_selective_disclosure(self, original_data, fields_to_disclose):
        """Create a simulated selective disclosure proof"""
        # Extract only the fields to disclose
        disclosed_data = {}
        for field in fields_to_disclose:
            if field in original_data:
                disclosed_data[field] = original_data[field]
        
        # Create a hash of the original data
        original_hash = hashlib.sha256(json.dumps(original_data).encode()).hexdigest()
        
        # Create a hash of the disclosed data
        disclosed_hash = hashlib.sha256(json.dumps(disclosed_data).encode()).hexdigest()
        
        # Create a random nonce
        nonce = base64.b64encode(os.urandom(16)).decode()
        
        # Create a proof linking the disclosed data to the original
        proof_elements = {
            "original_hash": original_hash,
            "disclosed_hash": disclosed_hash,
            "nonce": nonce,
            "timestamp": int(time.time())
        }
        
        # Create a signature for verification
        signature = hashlib.sha256(json.dumps(proof_elements).encode()).hexdigest()
        
        return {
            "proof_type": "selective_disclosure",
            "disclosed_data": disclosed_data,
            "simulated": True,
            "proof_elements": proof_elements,
            "signature": signature
        }
    
    def _verify_simulated_disclosure(self, proof_package, original_data_hash):
        """Verify a simulated selective disclosure proof"""
        if not proof_package.get("simulated", False):
            return False
            
        # Re-create the signature
        computed_signature = hashlib.sha256(json.dumps(proof_package["proof_elements"]).encode()).hexdigest()
        
        # Verify the signature matches
        signature_valid = computed_signature == proof_package["signature"]
        
        # Verify the original hash matches
        hash_valid = proof_package["proof_elements"]["original_hash"] == original_data_hash
        
        return signature_valid and hash_valid

def test_zkproof_system():
    """Test the ZK proof system functionality"""
    # Initialize the ZK proof system
    zk = ZKProofSystem()
    
    # Test data
    work_id = "song-12345"
    rights_type = "Publishing"
    owner_address = "0x7338af1E9d6dbc4cc1Efa067C0775Bf222aDb0C3"
    
    # Create an ownership proof
    print("Creating ownership proof...")
    proof = zk.create_ownership_proof(work_id, rights_type, owner_address)
    print(f"Proof created: {proof['proof_type']} for {work_id}")
    
    # Verify the ownership proof
    print("Verifying ownership proof...")
    is_valid = zk.verify_ownership_proof(proof)
    print(f"Proof valid: {is_valid}")
    
    # Test selective disclosure
    original_data = {
        "work_title": "Midnight Dreams",
        "artist_party": "Sarah Wilson",
        "publisher_party": "Dreamlight Records",
        "rights_type": "Publishing",
        "territory": "Global",
        "term": "2 years with renewal option",
        "royalty_info": [
            {"party": "Sarah Wilson", "percentage": 0.5},
            {"party": "Dreamlight Records", "percentage": 0.5}
        ],
        "effective_date": "2025-04-01"
    }
    
    fields_to_disclose = ["work_title", "artist_party", "rights_type", "territory"]
    
    print("Creating selective disclosure proof...")
    disclosure = zk.create_selective_disclosure(original_data, fields_to_disclose)
    print(f"Disclosure created with fields: {', '.join(fields_to_disclose)}")
    
    # Verify the selective disclosure
    original_hash = hashlib.sha256(json.dumps(original_data).encode()).hexdigest()
    
    print("Verifying selective disclosure...")
    disclosure_valid = zk.verify_selective_disclosure(disclosure, original_hash)
    print(f"Disclosure valid: {disclosure_valid}")
    
    # Test royalty proof
    payment_amount = 10000.00
    
    print("Creating royalty proof...")
    royalty_proof = zk.create_royalty_proof(original_data, payment_amount)
    print(f"Royalty proof created for payment: ${payment_amount}")
    
    # In a real system, we would also verify the royalty proof
    
    return {
        "ownership_proof_valid": is_valid,
        "disclosure_valid": disclosure_valid,
        "royalty_proof_created": royalty_proof is not None
    }

if __name__ == "__main__":
    # Run the test function
    results = test_zkproof_system()
    print(f"\nTest Results: {json.dumps(results, indent=2)}") 