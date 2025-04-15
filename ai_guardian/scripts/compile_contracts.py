#!/usr/bin/env python3

import json
import os
from solcx import compile_standard, install_solc

def compile_contracts():
    """Compile all contracts in the src directory"""
    print("Installing solc 0.8.19...")
    install_solc("0.8.19")
    
    src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
    build_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "build")
    
    # Create build directory if it doesn't exist
    os.makedirs(build_dir, exist_ok=True)
    
    # Get all Solidity files and their content
    sources = {}
    for file in os.listdir(src_dir):
        if file.endswith(".sol"):
            with open(os.path.join(src_dir, file), "r") as f:
                sources[file] = {"content": f.read()}
    
    print("\nCompiling contracts...")
    # Compile all contracts together
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": sources,
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": [
                            "abi",
                            "metadata",
                            "evm.bytecode",
                            "evm.sourceMap"
                        ]
                    }
                },
                "optimizer": {
                    "enabled": True,
                    "runs": 200
                }
            }
        },
        solc_version="0.8.19"
    )
    
    # Save each contract's output
    for contract_file in sources:
        contract_name = contract_file[:-4]  # Remove .sol extension
        
        # Get the compiled contract
        try:
            contract_data = compiled_sol["contracts"][contract_file][contract_name]
            
            # Prepare output data
            output_data = {
                "abi": contract_data["abi"],
                "bytecode": contract_data["evm"]["bytecode"]["object"],
                "metadata": contract_data["metadata"]
            }
            
            # Save to build directory
            output_path = os.path.join(build_dir, f"{contract_name}.json")
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)
            
            print(f"✅ {contract_name} compiled successfully!")
            
        except KeyError:
            print(f"⚠️ Skipping {contract_name} - not a contract or compilation failed")

if __name__ == "__main__":
    print("=== Compiling Contracts ===")
    compile_contracts()
    print("\n=== Compilation Complete ===")
    print("Contract artifacts saved in build directory") 