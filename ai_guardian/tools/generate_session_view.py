#!/usr/bin/env python3

import os
import json
import sys
import argparse
import shutil
from datetime import datetime

def load_session_data(session_dir):
    """Load session data from a specific session directory"""
    # Find the final report file
    report_dir = os.path.join(session_dir, "reports")
    report_files = [f for f in os.listdir(report_dir) if f.startswith("final_report")]
    
    if not report_files:
        print(f"No final report found in {report_dir}")
        sys.exit(1)
    
    # Load the final report
    report_path = os.path.join(report_dir, report_files[0])
    with open(report_path, 'r') as f:
        report_data = json.load(f)
    
    # Load discovery files
    discoveries_dir = os.path.join(session_dir, "discoveries")
    discovery_files = [f for f in os.listdir(discoveries_dir) if f.endswith(".json")]
    
    discoveries = []
    for df in discovery_files:
        with open(os.path.join(discoveries_dir, df), 'r') as f:
            try:
                discovery = json.load(f)
                discoveries.append(discovery)
            except json.JSONDecodeError:
                print(f"Error parsing discovery file: {df}")
    
    # Create a complete session data object
    session_data = {
        "session_id": report_data.get("session_id", "unknown"),
        "session_start_time": report_data.get("session_start_time", ""),
        "session_duration_hours": report_data.get("session_duration_hours", 0),
        "generation_time": report_data.get("generation_time", ""),
        "agency_identifier": "MESA Rights Vault",
        "statistics": report_data.get("statistics", {}),
        "all_discoveries": discoveries,
        "all_funds": report_data.get("discovered_funds", []),
        "highest_value_discoveries": report_data.get("highest_value_discoveries", []),
        "agency_attribution": {
            "agency": "MESA Rights Vault AI Guardian",
            "discovery_method": "AI-powered rights auditing",
            "attribution_strength": "High",
            "digital_signature": "MESA-" + report_data.get("session_id", "unknown")
        }
    }
    
    return session_data

def generate_html_view(session_data, output_path):
    """Generate an HTML view from the session data"""
    # Read the template HTML file
    template_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(template_dir, "templates", "session_collector_viewer.html")
    
    if not os.path.exists(template_path):
        print(f"Template file not found: {template_path}")
        sys.exit(1)
        
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Replace the placeholder with actual JSON data
    json_data = json.dumps(session_data, indent=2)
    html_content = template_content.replace("SESSION_DATA_PLACEHOLDER", json_data)
    
    # Write the output file
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Generated HTML view at: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate HTML visualization for session collector data")
    parser.add_argument("session_dir", help="Path to the session directory to visualize")
    parser.add_argument("--output", "-o", help="Output HTML file path (default: session_view.html in current directory)")
    
    args = parser.parse_args()
    
    # Check if session directory exists
    if not os.path.isdir(args.session_dir):
        print(f"Session directory not found: {args.session_dir}")
        sys.exit(1)
    
    # Load session data
    session_data = load_session_data(args.session_dir)
    
    # Determine output path
    output_path = args.output if args.output else os.path.join(os.getcwd(), "session_view.html")
    
    # Generate HTML view
    generate_html_view(session_data, output_path)
    
    print(f"\nTo view the report, open: {output_path}")

if __name__ == "__main__":
    main() 