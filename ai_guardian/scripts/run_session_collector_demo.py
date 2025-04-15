#!/usr/bin/env python3

import sys
import os
import json
import logging
import argparse
import time
import signal
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import our modules
from models.royalty_auditor.session_collector import SessionCollector
from models.royalty_auditor.auditor import RoyaltyAuditor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("Stopping session collector (Ctrl+C detected)")
    global collector
    if collector and collector.is_running:
        collector.stop_collection()
    sys.exit(0)

def generate_sample_catalog():
    """Generate sample catalog data for demonstration"""
    from models.royalty_auditor.pro_integration import PROIntegration
    pro_integration = PROIntegration()
    
    # For demo purposes, create a larger catalog with more works
    catalog = {
        "rights_holder": "Demo Artist",
        "catalog_id": f"CAT-DEMO-{int(time.time())}",
        "works": []
    }
    
    # Generate a variety of works
    work_titles = [
        "Summer Breeze", "Midnight Symphony", "Ocean Waves", 
        "Mountain Echo", "City Lights", "Desert Wind",
        "Forest Rain", "River Flow", "Sunset Dreams",
        "Morning Rise", "Evening Star", "Winter Snow"
    ]
    
    writers = [
        {"name": "John A. Smith", "role": "Composer"},
        {"name": "Jane B. Doe", "role": "Lyricist"},
        {"name": "Michael C. Johnson", "role": "Producer"},
        {"name": "Sarah D. Williams", "role": "Arranger"}
    ]
    
    publishers = [
        "Melody Publishing Co.", 
        "Rhythm Rights Inc.",
        "Harmony Holdings LLC",
        "Sonic Ventures"
    ]
    
    # Generate works
    for i, title in enumerate(work_titles):
        work_id = f"WORK{i+100}"
        isrc = f"US-AB1-23-{i+1000:05d}"
        iswc = f"T-12345{i+1:04d}-1"
        
        # Select writers (1-3 per work)
        work_writers = []
        writer_count = min(3, (i % 4) + 1)  # 1-3 writers
        
        # Assign shares based on writer count
        share_per_writer = 100 // writer_count
        remaining_share = 100 % writer_count
        
        for j in range(writer_count):
            writer_idx = (i + j) % len(writers)
            writer = writers[writer_idx].copy()
            writer["share"] = f"{share_per_writer + (1 if j < remaining_share else 0)}%"
            work_writers.append(writer)
        
        # Select publisher
        publisher = publishers[i % len(publishers)]
        
        # Create the work
        work = {
            "id": work_id,
            "title": title,
            "writers": work_writers,
            "isrc": isrc,
            "iswc": iswc,
            "publisher": publisher
        }
        
        catalog["works"].append(work)
    
    return catalog

def run_session_collector_demo(runtime_minutes=5, accelerated=False, verbose=False):
    """
    Run the session collector demo
    
    Args:
        runtime_minutes: How long to run the demo (in minutes)
        accelerated: Whether to use accelerated timing for demo purposes
        verbose: Whether to enable verbose logging
    """
    global collector
    
    # Set up logging
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info(f"Starting Session Collector Demo (runtime: {runtime_minutes} minutes)")
    
    # Create output directories
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    sessions_dir = Path(__file__).parent.parent / "sessions"
    sessions_dir.mkdir(exist_ok=True)
    
    # Create custom configuration for demo purposes
    config = {
        # For demo purposes, use much shorter intervals if accelerated
        "collection_intervals": {
            "quick_scan": 1 if accelerated else 15,  # Every 1 min in accelerated mode
            "detailed_scan": 2 if accelerated else 120,  # Every 2 mins in accelerated mode
            "deep_analysis": 4 if accelerated else 1440,  # Every 4 mins in accelerated mode
        },
        "monitored_pros": [
            "ascap", "bmi", "sesac", "soundexchange", 
            "hfa", "mlc"
        ],
        "monitored_platforms": [
            "spotify", "apple_music", "youtube", "amazon_music",
            "tidal"
        ],
        "agency_identifier": "MESA-DEMO-AGENCY",
        "generate_interim_reports": True,
        "report_interval": 3 if accelerated else 60  # Every 3 mins in accelerated mode
    }
    
    # Save config
    config_file = output_dir / "demo_collector_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Demo configuration saved to {config_file}")
    
    # Generate sample catalog
    catalog = generate_sample_catalog()
    catalog_file = output_dir / "demo_catalog.json"
    with open(catalog_file, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    logger.info(f"Demo catalog with {len(catalog['works'])} works saved to {catalog_file}")
    
    # Initialize the session collector
    collector = SessionCollector(config_path=str(config_file))
    
    # Start collection
    collector.start_collection(run_immediately=True)
    logger.info(f"Collection started in session {collector.session_id}")
    logger.info(f"Session data directory: {collector.session_dir}")
    
    # Run a targeted scan on the sample catalog
    logger.info("Running targeted scan on the sample catalog")
    targeted_results = collector.scan_specific_catalog(catalog)
    logger.info(f"Targeted scan completed with {len(targeted_results['discoveries'])} discoveries")
    
    # Main loop - run for specified duration
    end_time = time.time() + (runtime_minutes * 60)
    try:
        while time.time() < end_time and collector.is_running:
            # Display current status every 30 seconds
            summary = collector.get_session_summary()
            logger.info(f"Session running for {summary['duration_hours']:.2f} hours, " +
                       f"discovered {summary['total_discoveries']} issues worth {summary['total_value']}")
            
            # Sleep for 30 seconds
            time.sleep(30)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected")
    finally:
        # Stop collection and generate final report
        logger.info("Stopping collection and generating final report")
        collector.stop_collection()
    
    # Display final summary
    final_summary = collector.get_session_summary()
    logger.info("\n=== FINAL SESSION SUMMARY ===")
    logger.info(f"Session ID: {final_summary['session_id']}")
    logger.info(f"Session duration: {final_summary['duration_hours']:.2f} hours")
    logger.info(f"Total discoveries: {final_summary['total_discoveries']}")
    logger.info(f"Total potential funds: {final_summary['total_funds']}")
    logger.info(f"Total potential value: {final_summary['total_value']}")
    logger.info(f"Session data directory: {collector.session_dir}")
    
    # Copy final report to output directory for easy access
    final_reports = list(Path(collector.session_dir / "reports").glob("final_report_*.json"))
    if final_reports:
        final_report = final_reports[0]
        final_report_copy = output_dir / f"session_{collector.session_id[:8]}_final_report.json"
        with open(final_report, 'r') as src, open(final_report_copy, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Final report copied to: {final_report_copy}")
    
    return {
        "session_id": collector.session_id,
        "session_dir": str(collector.session_dir),
        "final_summary": final_summary
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Session Collector Demo")
    parser.add_argument("--runtime", type=int, default=5, help="Runtime in minutes (default: 5)")
    parser.add_argument("--accelerated", action="store_true", help="Use accelerated timing for demo")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    # Global variable for signal handler
    collector = None
    
    result = run_session_collector_demo(
        runtime_minutes=args.runtime,
        accelerated=args.accelerated,
        verbose=args.verbose
    ) 