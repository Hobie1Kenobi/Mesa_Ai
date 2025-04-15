#!/usr/bin/env python3

import os
import json
import hashlib
import random
import time
import argparse
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('zk_training.log')
    ]
)

class ZKTrainer:
    """
    Trainer for zero-knowledge proof generation and testing
    """
    
    def __init__(self, config_path, output_dir=None):
        """Initialize the ZK trainer with configuration"""
        self.config_path = Path(config_path)
        
        # Load configuration
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        
        # Set output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path('output')
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up circuit directories
        self.circuits_dir = Path('circuit_templates')
        
        # Internal state
        self.training_data = {}
        self.trained_circuits = {}
    
    def load_sample_data(self, data_path):
        """Load sample data for training"""
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        logging.info(f"Loaded {len(data.get('rights', []))} rights records from {data_path}")
        self.sample_data = data
        return data
    
    def generate_training_samples(self, proof_type, num_samples):
        """Generate training samples for a specific proof type"""
        logging.info(f"Generating {num_samples} training samples for {proof_type}")
        
        samples = []
        
        if proof_type == "ownership_proof":
            for _ in range(num_samples):
                # Select a random right from the sample data or generate synthetic if needed
                if hasattr(self, 'sample_data') and random.random() < 0.7:
                    # Use existing sample 70% of the time
                    right = random.choice(self.sample_data.get('rights', []))
                    work_id = right.get('workTitle', 'Unknown Work')
                    rights_type = right.get('rightsType', 'Unknown Type')
                    owner_address = right.get('rightId', '0x0')  # Using rightId as stand-in for address
                else:
                    # Generate synthetic data
                    work_id = f"Work-{random.randint(10000, 99999)}"
                    rights_type = random.choice(["Publishing", "Performance", "Mechanical", "Sync", "Master"])
                    owner_address = f"0x{random.randint(0, 2**160):040x}"
                
                # Generate a random salt
                salt = random.randint(1, 2**64)
                
                # Create the sample
                sample = {
                    "private_inputs": {
                        "workId": self._field_element(work_id),
                        "rightsType": self._field_element(rights_type),
                        "ownerAddress": self._field_element(owner_address),
                        "salt": salt
                    }
                }
                
                # Calculate the public inputs (hashes)
                sample["public_inputs"] = {
                    "workIdHash": self._hash_with_salt(work_id, salt),
                    "rightsTypeHash": self._hash_with_salt(rights_type, salt),
                    "ownerAddressHash": self._hash_with_salt(owner_address, salt)
                }
                
                samples.append(sample)
        
        elif proof_type == "selective_disclosure":
            for _ in range(num_samples):
                # Generate or select a complete set of rights data
                if hasattr(self, 'sample_data') and random.random() < 0.7:
                    right = random.choice(self.sample_data.get('rights', []))
                else:
                    # Generate synthetic complete data (simplified)
                    right = {
                        "workTitle": f"Work-{random.randint(10000, 99999)}",
                        "artistParty": f"Artist-{random.randint(1000, 9999)}",
                        "publisherParty": f"Publisher-{random.randint(1000, 9999)}",
                        "rightsType": random.choice(["Publishing", "Performance", "Mechanical", "Sync", "Master"]),
                        "territory": random.choice(["Global", "US", "EU", "UK", "Asia"]),
                        "royaltyInfo": [
                            {"party": "Party1", "percentage": 0.6},
                            {"party": "Party2", "percentage": 0.4}
                        ]
                    }
                
                # Convert to string representation for ZK circuit
                original_data = self._field_element(json.dumps(right))
                
                # Select random fields to disclose
                all_fields = list(right.keys())
                num_to_disclose = random.randint(1, len(all_fields))
                disclosed_fields = random.sample(all_fields, num_to_disclose)
                
                # Create disclosed subset
                disclosed_subset = {field: right[field] for field in disclosed_fields}
                
                # Create undisclosed subset (complement)
                undisclosed_fields = [f for f in all_fields if f not in disclosed_fields]
                undisclosed_subset = {field: right[field] for field in undisclosed_fields}
                
                # Convert to field elements
                disclosed_data = self._field_element(json.dumps(disclosed_subset))
                undisclosed_data = self._field_element(json.dumps(undisclosed_subset))
                
                # Generate salt
                salt = random.randint(1, 2**64)
                
                # Create the sample
                sample = {
                    "private_inputs": {
                        "originalData": original_data,
                        "disclosedFields": disclosed_data,
                        "undisclosedFields": undisclosed_data,
                        "salt": salt
                    }
                }
                
                # Calculate public inputs
                sample["public_inputs"] = {
                    "originalDataHash": self._hash_with_salt(json.dumps(right), salt),
                    "disclosedFieldsHash": self._hash_with_salt(json.dumps(disclosed_subset), salt)
                }
                
                samples.append(sample)
        
        elif proof_type == "royalty_proof":
            for _ in range(num_samples):
                # Number of parties
                num_parties = random.randint(2, 5)
                
                # Generate royalty percentages that sum to 1.0
                percentages = self._generate_distribution(num_parties)
                
                # Generate party IDs
                party_ids = [random.randint(1, 2**32) for _ in range(num_parties)]
                
                # Payment amount
                payment_amount = random.randint(100, 10000)
                
                # Calculate expected payments
                expected_payments = [round(payment_amount * p, 2) for p in percentages]
                
                # Generate salt
                salt = random.randint(1, 2**64)
                
                # Create sample
                sample = {
                    "private_inputs": {
                        "royaltyPercentages": percentages,
                        "partyIds": party_ids,
                        "expectedPayments": expected_payments,
                        "salt": salt
                    }
                }
                
                # Calculate public inputs
                sample["public_inputs"] = {
                    "paymentAmount": payment_amount,
                    "totalRoyaltyHash": self._hash_with_salt(sum(percentages), salt),
                    "partiesCountHash": self._hash_with_salt(num_parties, salt),
                    "expectedPaymentHash": self._hash_with_salt(sum(expected_payments), salt)
                }
                
                samples.append(sample)
        
        else:
            logging.warning(f"Unknown proof type: {proof_type}")
            return []
        
        logging.info(f"Generated {len(samples)} samples for {proof_type}")
        self.training_data[proof_type] = samples
        return samples
    
    def compile_circuit(self, circuit_name):
        """Compile a circuit for training"""
        circuit_path = self.circuits_dir / f"{circuit_name}.circom"
        if not circuit_path.exists():
            logging.error(f"Circuit file {circuit_path} not found")
            return False
        
        try:
            # Create output directory for compiled circuit
            circuit_output = self.output_dir / circuit_name
            circuit_output.mkdir(parents=True, exist_ok=True)
            
            # Full path to output R1CS file
            r1cs_path = circuit_output / f"{circuit_name}.r1cs"
            
            # Only compile if R1CS doesn't exist or is outdated
            if not r1cs_path.exists() or os.path.getmtime(circuit_path) > os.path.getmtime(r1cs_path):
                logging.info(f"Compiling circuit: {circuit_name}")
                
                # Command to compile the circuit with Circom
                # This is a simulation - in a real implementation, you'd run circom
                logging.info(f"[SIMULATION] circom {circuit_path} --r1cs --wasm --output {circuit_output}")
                
                # In a real implementation, you would run:
                # subprocess.run(
                #     ["circom", str(circuit_path), "--r1cs", "--wasm", "--output", str(circuit_output)],
                #     check=True
                # )
                
                # For the simulation, create a dummy file
                with open(r1cs_path, 'w') as f:
                    f.write(f"# Simulated R1CS for {circuit_name}\n")
                
                # Generate dummy witness generator file
                wasm_dir = circuit_output / f"{circuit_name}_js"
                wasm_dir.mkdir(parents=True, exist_ok=True)
                with open(wasm_dir / f"{circuit_name}.wasm", 'w') as f:
                    f.write(f"# Simulated WASM for {circuit_name}\n")
            
            # Set up proving and verification keys (simulation)
            zkey_path = circuit_output / f"{circuit_name}.zkey"
            vkey_path = circuit_output / f"{circuit_name}.vkey.json"
            
            if not zkey_path.exists():
                logging.info(f"Generating proving key for: {circuit_name}")
                
                # In a real implementation:
                # 1. Generate powers of tau
                # 2. Create zkey file
                # 3. Export verification key
                
                # For simulation, create dummy files
                with open(zkey_path, 'w') as f:
                    f.write(f"# Simulated zkey for {circuit_name}\n")
                
                vkey_data = {
                    "protocol": "groth16",
                    "curve": "bn128",
                    "nPublic": 3,  # Varies by circuit
                    "vk_alpha_1": ["0", "0", "0"],
                    "vk_beta_2": [["0", "0"], ["0", "0"], ["0", "0"]],
                    "vk_gamma_2": [["0", "0"], ["0", "0"], ["0", "0"]],
                    "vk_delta_2": [["0", "0"], ["0", "0"], ["0", "0"]],
                    "vk_alphabeta_12": [["0", "0"], ["0", "0"], ["0", "0"]]
                }
                
                with open(vkey_path, 'w') as f:
                    json.dump(vkey_data, f, indent=2)
            
            self.trained_circuits[circuit_name] = {
                "r1cs_path": r1cs_path,
                "wasm_dir": wasm_dir,
                "zkey_path": zkey_path,
                "vkey_path": vkey_path
            }
            
            return True
            
        except Exception as e:
            logging.error(f"Error compiling circuit: {e}")
            return False
    
    def generate_proofs(self, proof_type, num_proofs=10):
        """Generate sample ZK proofs using the compiled circuits"""
        if proof_type not in self.training_data:
            logging.error(f"No training data for {proof_type}")
            return []
        
        circuit_info = self.trained_circuits.get(self.config["zk_proof_types"][proof_type]["circuit"].replace(".circom", ""))
        if not circuit_info:
            logging.error(f"Circuit for {proof_type} not compiled")
            return []
        
        # Select a subset of samples to generate proofs for
        samples = random.sample(self.training_data[proof_type], min(num_proofs, len(self.training_data[proof_type])))
        
        proofs = []
        for i, sample in enumerate(samples):
            try:
                logging.info(f"Generating proof {i+1}/{len(samples)} for {proof_type}")
                
                # In a real implementation, you would:
                # 1. Generate witness from inputs
                # 2. Generate proof using zkey
                # 3. Verify the proof
                
                # For simulation, create a dummy proof
                proof = {
                    "pi_a": ["0", "0", "0"],
                    "pi_b": [["0", "0"], ["0", "0"], ["0", "0"]],
                    "pi_c": ["0", "0", "0"],
                    "protocol": "groth16",
                    "curve": "bn128"
                }
                
                public_inputs = list(sample["public_inputs"].values())
                
                # Create the full proof record
                proof_record = {
                    "proof": proof,
                    "public_inputs": public_inputs,
                    "verified": True,
                    "proof_type": proof_type,
                    "timestamp": int(time.time())
                }
                
                proofs.append(proof_record)
                
            except Exception as e:
                logging.error(f"Error generating proof: {e}")
        
        return proofs
    
    def save_results(self):
        """Save training results"""
        # Save training data samples
        for proof_type, samples in self.training_data.items():
            output_path = self.output_dir / f"{proof_type}_samples.json"
            with open(output_path, 'w') as f:
                json.dump(samples, f, indent=2)
            logging.info(f"Saved {len(samples)} training samples to {output_path}")
        
        # Save circuit information
        circuits_info = {}
        for name, info in self.trained_circuits.items():
            circuits_info[name] = {
                "r1cs_path": str(info["r1cs_path"]),
                "wasm_dir": str(info["wasm_dir"]),
                "zkey_path": str(info["zkey_path"]),
                "vkey_path": str(info["vkey_path"])
            }
        
        circuits_path = self.output_dir / "compiled_circuits.json"
        with open(circuits_path, 'w') as f:
            json.dump(circuits_info, f, indent=2)
        logging.info(f"Saved circuit information to {circuits_path}")
    
    def _field_element(self, value):
        """Convert a value to a field element representation"""
        # For non-numeric values, hash them to get a numeric representation
        if isinstance(value, str):
            return int(hashlib.sha256(value.encode()).hexdigest(), 16) % (2**64)
        elif isinstance(value, int):
            return value
        else:
            return int(hashlib.sha256(str(value).encode()).hexdigest(), 16) % (2**64)
    
    def _hash_with_salt(self, value, salt):
        """Create a salted hash of a value"""
        # For Poseidon simulation - in production, use actual Poseidon hash
        combined = f"{value}:{salt}"
        return int(hashlib.sha256(combined.encode()).hexdigest(), 16) % (2**64)
    
    def _generate_distribution(self, n, sum_to=1.0):
        """Generate n random values that sum to the specified value"""
        values = [random.random() for _ in range(n)]
        total = sum(values)
        return [round(v * sum_to / total, 4) for v in values]
    
    def run_training(self):
        """Run the complete training process"""
        # Generate training samples for each proof type
        for proof_type, config in self.config["zk_proof_types"].items():
            num_samples = config.get("training_samples", 100)
            self.generate_training_samples(proof_type, num_samples)
            
            # Compile the circuit
            circuit_name = config["circuit"].replace(".circom", "")
            self.compile_circuit(circuit_name)
            
            # Generate sample proofs
            self.generate_proofs(proof_type, 10)
        
        # Save all results
        self.save_results()
        
        logging.info("Training completed successfully")

def main():
    """Main function to run the training script"""
    parser = argparse.ArgumentParser(description="Train zero-knowledge proof circuits")
    parser.add_argument("--config", default="zk_training_config.json", help="Path to the training config file")
    parser.add_argument("--samples", default="sample_music_rights.json", help="Path to sample data file")
    parser.add_argument("--output", default="training_output", help="Output directory")
    args = parser.parse_args()
    
    trainer = ZKTrainer(args.config, args.output)
    trainer.load_sample_data(args.samples)
    trainer.run_training()

if __name__ == "__main__":
    main() 