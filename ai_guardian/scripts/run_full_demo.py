#!/usr/bin/env python3

import os
import argparse
import logging
import time
import webbrowser
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_full_demo(open_browser=True):
    """Run the full unified IP container demo with visualization"""
    # Import modules
    from unified_ip_container_demo import run_unified_ip_demo
    from generate_demo_html import generate_html
    
    logger.info("Starting Full Unified IP Container Demo")
    
    # Step 1: Run demo to generate JSON data
    demo_data, json_file = run_unified_ip_demo()
    
    # Step 2: Create directories
    templates_dir = Path(__file__).parent.parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Step 3: Generate HTML visualization
    html_file = generate_html(json_file)
    
    # Step 4: Open in browser if requested
    if open_browser:
        logger.info(f"Opening visualization in web browser")
        # Convert to file URL with correct format
        file_url = f"file://{os.path.abspath(html_file)}"
        webbrowser.open(file_url)
    
    logger.info("Full demo completed successfully")
    logger.info(f"Demo data: {json_file}")
    logger.info(f"Visualization: {html_file}")
    
    return {
        "demo_data": demo_data,
        "json_file": json_file,
        "html_file": html_file
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Full Unified IP Container Demo")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser visualization")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    run_full_demo(not args.no_browser) 