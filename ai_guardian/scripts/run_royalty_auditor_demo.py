#!/usr/bin/env python3

import sys
import os
import json
import logging
import argparse
from pathlib import Path
import time
import random

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import our modules
from models.royalty_auditor.auditor import RoyaltyAuditor
from models.royalty_auditor.pro_integration import PROIntegration
from models.royalty_auditor.metadata_matcher import MetadataMatcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_sample_catalog() -> dict:
    """Generate a sample music catalog for demonstration"""
    return {
        "rights_holder": "Sample Artist",
        "catalog_id": "CAT-2023-001",
        "works": [
            {
                "id": "WORK123",
                "title": "Sample Song Title",
                "writers": [
                    {"name": "John A. Smith", "role": "Composer", "share": "50%"},
                    {"name": "Jane B. Doe", "role": "Lyricist", "share": "50%"}
                ],
                "isrc": "US-AB1-23-00001",
                "iswc": "T-123456789-1",
                "publisher": "Sample Music Publishing"
            },
            {
                "id": "WORK456",
                "title": "Another Example Track",
                "writers": [
                    {"name": "John A. Smith", "role": "Composer", "share": "100%"}
                ],
                "isrc": "US-AB1-23-00002",
                "iswc": "T-123456790-2",
                "publisher": "Sample Music Publishing"
            }
        ]
    }

def generate_sample_statement() -> dict:
    """Generate a sample royalty statement with errors for demonstration"""
    return {
        "statement_id": "BMI-2023-Q1",
        "period": "January-March 2023",
        "rights_holder": "Sample Artist",
        "payments": [
            {
                "work_title": "Sample Snog Title",  # Deliberate error
                "writer": "John Smith",  # Missing middle initial
                "isrc": "US-AB1-23-00001",
                "usage_type": "Streaming",
                "plays": 15000,
                "amount": "$120.50"
            }
            # Note: The second song is missing entirely from the statement
        ]
    }

def run_royalty_auditor_demo(verbose=False):
    """Run the AI Royalty Auditor demo"""
    
    # Set up logging
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting AI Royalty Auditor Demo")
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Initialize our components
    auditor = RoyaltyAuditor()
    pro_integration = PROIntegration()
    matcher = MetadataMatcher()
    
    # Create sample data
    catalog = generate_sample_catalog()
    statement = generate_sample_statement()
    
    # Save sample data
    catalog_file = output_dir / "sample_catalog.json"
    statement_file = output_dir / "sample_statement.json"
    
    with open(catalog_file, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    with open(statement_file, 'w') as f:
        json.dump(statement, f, indent=2)
    
    logger.info(f"Generated sample catalog: {catalog_file}")
    logger.info(f"Generated sample statement: {statement_file}")
    
    # Demo 1: Perform royalty audit
    logger.info("\n=== DEMO 1: ROYALTY STATEMENT AUDIT ===")
    logger.info("Auditing royalty statement against verified catalog data...")
    time.sleep(1)  # Simulate processing time
    
    audit_results = auditor.audit_royalty_statement(str(statement_file), catalog)
    
    audit_file = output_dir / "audit_results.json"
    with open(audit_file, 'w') as f:
        json.dump(audit_results, f, indent=2)
    
    logger.info(f"Audit completed: {audit_file}")
    logger.info(f"Found {audit_results['summary']['discrepancies_found']} discrepancies")
    logger.info(f"Estimated recovery value: {audit_results['summary']['estimated_recovery_value']}")
    
    # Demo 2: Metadata correction
    logger.info("\n=== DEMO 2: METADATA CORRECTION ===")
    logger.info("Generating metadata corrections for submission to PROs...")
    time.sleep(1)  # Simulate processing time
    
    # Get the first discrepancy as an example
    discrepancy = audit_results['discrepancies'][1]  # Metadata mismatch
    
    # Demo metadata correction
    corrections = {
        "writer": {
            "from": "John Smith",
            "to": "John A. Smith"
        }
    }
    
    correction_results = auditor.fix_metadata("WORK123", corrections)
    
    correction_file = output_dir / "metadata_corrections.json"
    with open(correction_file, 'w') as f:
        json.dump(correction_results, f, indent=2)
    
    logger.info(f"Metadata corrections generated: {correction_file}")
    
    # Demo 3: Check for black box funds
    logger.info("\n=== DEMO 3: BLACK BOX FUNDS CHECK ===")
    logger.info("Checking PROs for unclaimed black box funds...")
    time.sleep(1)  # Simulate processing time
    
    # Check for black box funds for the first work
    identifier = {
        "type": "isrc", 
        "value": catalog["works"][0]["isrc"]
    }
    
    black_box_results = pro_integration.check_black_box_funds(identifier, "soundexchange")
    
    black_box_file = output_dir / "black_box_check.json"
    with open(black_box_file, 'w') as f:
        json.dump(black_box_results, f, indent=2)
    
    logger.info(f"Black box check completed: {black_box_file}")
    if black_box_results["has_unclaimed_funds"]:
        logger.info(f"Found unclaimed funds: {black_box_results['estimated_amount']}")
    
    # Demo 4: Full catalog analysis
    logger.info("\n=== DEMO 4: FULL CATALOG ANALYSIS ===")
    logger.info("Analyzing full catalog for recovery opportunities...")
    time.sleep(2)  # Simulate longer processing time
    
    catalog_analysis = auditor.analyze_catalog(catalog)
    
    analysis_file = output_dir / "catalog_analysis.json"
    with open(analysis_file, 'w') as f:
        json.dump(catalog_analysis, f, indent=2)
    
    logger.info(f"Catalog analysis completed: {analysis_file}")
    logger.info(f"Found {len(catalog_analysis['recovery_opportunities'])} recovery opportunities")
    logger.info(f"Total estimated recovery: {catalog_analysis['summary']['total_estimated_recovery']}")
    
    # Generate comprehensive report
    report = {
        "timestamp": time.time(),
        "audit_results": audit_results,
        "metadata_corrections": correction_results,
        "black_box_funds": black_box_results,
        "catalog_analysis": catalog_analysis,
        "summary": {
            "total_works": len(catalog["works"]),
            "works_with_issues": len(catalog_analysis["recovery_opportunities"]),
            "total_estimated_recovery": catalog_analysis["summary"]["total_estimated_recovery"],
            "recommended_actions": [
                "Submit metadata corrections to ASCAP and BMI",
                "File claim for unclaimed SoundExchange royalties",
                "Register missing works with MLC"
            ]
        }
    }
    
    report_file = output_dir / "royalty_auditor_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"\nComprehensive report generated: {report_file}")
    
    return {
        "report_file": str(report_file),
        "audit_results": audit_results,
        "metadata_corrections": correction_results,
        "black_box_check": black_box_results,
        "catalog_analysis": catalog_analysis
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the AI Royalty Auditor Demo")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    run_royalty_auditor_demo(args.verbose) 