#!/usr/bin/env python3
"""
MESA Rights Vault - Discogs Import Demonstration Script

This script demonstrates how to run the Discogs data pull and work with the resulting data
while respecting privacy controls. It shows three main functionalities:
1. Running the data pull script with appropriate configuration
2. Accessing the pulled data with different privacy levels
3. Generating a summary report of imported data

Usage:
    python run_discogs_import.py --config config.json [--analyze]

Options:
    --config CONFIG       Path to configuration file (default: config.json)
    --analyze             Run data analysis after import

Example configuration file (config.json):
{
    "discogs_token": "YOUR_DISCOGS_API_TOKEN",
    "genres": ["Electronic", "Rock"],
    "artists": ["Aphex Twin"],
    "years": ["1990-1999"],
    "batch_size": 50,
    "max_items_per_category": 100,
    "output_dir": "discogs_data",
    "privacy_settings": {
        "enable_zk_proofs": true,
        "public_fields": ["rightId", "workTitle", "territory"],
        "private_fields": ["royaltyInfo", "publisherParty"],
        "selectively_disclosed_fields": {
            "artistParty": ["verifier1", "verifier2"],
            "effectiveDate": ["verifier1"]
        }
    }
}
"""

import os
import sys
import json
import time
import glob
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("discogs_import_demo.log")
    ]
)
logger = logging.getLogger("discogs_import_demo")

def check_dependencies() -> bool:
    """Check if required dependencies are installed"""
    try:
        import requests
        import tqdm
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.info("Please install required dependencies: pip install requests tqdm")
        return False

def run_data_pull(config_path: str) -> Dict[str, Any]:
    """Run the Discogs data pull script with the provided configuration"""
    logger.info(f"Starting Discogs data pull with config from {config_path}")
    
    # Check if the data pull script exists
    data_pull_script = Path(__file__).parent / "discogs_data_pull.py"
    
    if not data_pull_script.exists():
        logger.error(f"Data pull script not found at {data_pull_script}")
        raise FileNotFoundError(f"Data pull script not found at {data_pull_script}")
    
    try:
        # Option 1: Import and run the script directly
        script_path = str(data_pull_script)
        spec = importlib.util.spec_from_file_location("discogs_data_pull", script_path)
        data_pull_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_pull_module)
        
        # Create and run data puller
        data_puller = data_pull_module.DiscogsBulkDataPull(config_path)
        stats = data_puller.pull_data()
        
        logger.info(f"Data pull completed successfully")
        logger.info(f"Created {stats['total_rights_entries_created']} rights entries")
        
        # Load config to get output directory
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        output_dir = config.get("output_dir", "discogs_data")
        return {"stats": stats, "output_dir": output_dir}
        
    except Exception as e:
        logger.error(f"Error running data pull: {e}")
        raise

def demonstrate_data_access(output_dir: str) -> None:
    """Demonstrate how to access pulled data with privacy controls"""
    logger.info("Demonstrating data access with privacy controls")
    
    # Get all rights files
    rights_files = list(Path(output_dir).glob("right_*.json"))
    
    if not rights_files:
        logger.warning(f"No rights files found in {output_dir}")
        return
    
    logger.info(f"Found {len(rights_files)} rights entries")
    
    # Load a sample of rights entries (up to 5)
    sample_size = min(5, len(rights_files))
    sample_files = rights_files[:sample_size]
    
    for idx, file_path in enumerate(sample_files, 1):
        try:
            with open(file_path, 'r') as f:
                rights_entry = json.load(f)
            
            logger.info(f"\nAccess Demonstration #{idx}: {file_path.name}")
            
            # 1. Public access (only public fields)
            logger.info("PUBLIC ACCESS (available to anyone):")
            public_fields = ["rightId", "workTitle", "territory"]
            public_view = {field: rights_entry.get(field, "N/A") for field in public_fields}
            logger.info(f"  Public fields: {json.dumps(public_view, indent=2)}")
            
            # 2. Check if this entry has privacy controls
            has_privacy = "_privacy" in rights_entry
            logger.info(f"Privacy controls: {'ENABLED' if has_privacy else 'DISABLED'}")
            
            if has_privacy:
                # 3. Owner access (simulated - would require decryption)
                logger.info("OWNER ACCESS (requires authentication):")
                logger.info("  To access encrypted fields, owner would need to:")
                logger.info("  1. Authenticate with the system")
                logger.info("  2. Use their keys to decrypt the encrypted data")
                logger.info("  3. The following fields would be decrypted:")
                
                encrypted_fields = ["royaltyInfo", "publisherParty"]
                for field in encrypted_fields:
                    logger.info(f"    - {field}")
                
                # 4. Selective disclosure demonstration
                logger.info("SELECTIVE DISCLOSURE (for specific verifiers):")
                available_proofs = rights_entry.get("_privacy", {}).get("availableProofs", [])
                
                for proof in available_proofs:
                    if proof.get("type") == "selective_disclosure":
                        field = proof.get("field", "unknown")
                        verifiers = proof.get("allowedVerifiers", [])
                        logger.info(f"  Field '{field}' can be selectively disclosed to: {', '.join(verifiers)}")
        
        except Exception as e:
            logger.error(f"Error demonstrating access for {file_path}: {e}")

def analyze_pulled_data(output_dir: str) -> Dict[str, Any]:
    """Analyze the pulled data and generate a summary report"""
    logger.info(f"Analyzing pulled data in {output_dir}")
    
    # Get all rights files
    rights_files = list(Path(output_dir).glob("right_*.json"))
    
    if not rights_files:
        logger.warning(f"No rights files found in {output_dir}")
        return {"error": "No data found"}
    
    # Initialize analysis data
    analysis = {
        "total_entries": len(rights_files),
        "rights_types": {},
        "territories": {},
        "genres": {},
        "years": {},
        "artists": {},
        "publishers": {},
        "has_privacy": 0,
        "identifiers": {
            "ISWC": 0,
            "ISRC": 0
        }
    }
    
    # Process each file
    for file_path in rights_files:
        try:
            with open(file_path, 'r') as f:
                entry = json.load(f)
            
            # Count rights types
            rights_type = entry.get("rightsType")
            if rights_type:
                analysis["rights_types"][rights_type] = analysis["rights_types"].get(rights_type, 0) + 1
            
            # Count territories
            territory = entry.get("territory")
            if territory:
                if isinstance(territory, list):
                    for t in territory:
                        analysis["territories"][t] = analysis["territories"].get(t, 0) + 1
                else:
                    analysis["territories"][territory] = analysis["territories"].get(territory, 0) + 1
            
            # Count genres
            genres = entry.get("metadata", {}).get("genres", [])
            if genres:
                for genre in genres:
                    analysis["genres"][genre] = analysis["genres"].get(genre, 0) + 1
            
            # Count years
            year = entry.get("metadata", {}).get("year")
            if year and year != "Unknown":
                year_str = str(year)
                analysis["years"][year_str] = analysis["years"].get(year_str, 0) + 1
            
            # Count artists
            artist = entry.get("artistParty", {}).get("name")
            if artist:
                analysis["artists"][artist] = analysis["artists"].get(artist, 0) + 1
            
            # Count publishers
            publisher = entry.get("publisherParty", {}).get("name")
            if publisher:
                analysis["publishers"][publisher] = analysis["publishers"].get(publisher, 0) + 1
            
            # Count entries with privacy
            if "_privacy" in entry:
                analysis["has_privacy"] += 1
            
            # Count identifier types
            identifiers = entry.get("identifiers", {})
            if "ISWC" in identifiers:
                analysis["identifiers"]["ISWC"] += 1
            if "ISRC" in identifiers:
                analysis["identifiers"]["ISRC"] += 1
                
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
    
    # Calculate percentages
    total = len(rights_files)
    analysis["privacy_percentage"] = round((analysis["has_privacy"] / total) * 100, 2) if total > 0 else 0
    analysis["isrc_percentage"] = round((analysis["identifiers"]["ISRC"] / total) * 100, 2) if total > 0 else 0
    analysis["iswc_percentage"] = round((analysis["identifiers"]["ISWC"] / total) * 100, 2) if total > 0 else 0
    
    # Save analysis to file
    analysis_path = Path(output_dir) / "data_analysis.json"
    with open(analysis_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    logger.info(f"Analysis saved to {analysis_path}")
    
    # Log summary
    logger.info("\nAnalysis Summary:")
    logger.info(f"Total rights entries: {analysis['total_entries']}")
    logger.info(f"Entries with privacy controls: {analysis['has_privacy']} ({analysis['privacy_percentage']}%)")
    logger.info(f"Most common rights type: {max(analysis['rights_types'].items(), key=lambda x: x[1])[0]}")
    logger.info(f"Most common territory: {max(analysis['territories'].items(), key=lambda x: x[1])[0]}")
    
    if analysis["genres"]:
        logger.info(f"Top genres: {', '.join([k for k, v in sorted(analysis['genres'].items(), key=lambda x: x[1], reverse=True)[:3]])}")
    
    if analysis["artists"]:
        logger.info(f"Top artists: {', '.join([k for k, v in sorted(analysis['artists'].items(), key=lambda x: x[1], reverse=True)[:3]])}")
    
    return analysis

def main():
    """Main function to run the demonstration"""
    parser = argparse.ArgumentParser(description="Demonstrate Discogs data import for MESA Rights Vault")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    parser.add_argument("--analyze", action="store_true", help="Run data analysis after import")
    args = parser.parse_args()
    
    try:
        # Check dependencies
        logger.info("Checking dependencies...")
        if not check_dependencies():
            return 1
        
        # Run data pull
        logger.info("Running Discogs data pull...")
        result = run_data_pull(args.config)
        output_dir = result["output_dir"]
        
        # Demonstrate data access
        logger.info("\nDemonstrating data access...")
        demonstrate_data_access(output_dir)
        
        # Analyze data if requested
        if args.analyze:
            logger.info("\nAnalyzing pulled data...")
            analyze_pulled_data(output_dir)
        
        logger.info("\nDemonstration completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error during demonstration: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 