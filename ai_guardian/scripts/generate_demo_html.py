#!/usr/bin/env python3

import json
import argparse
import os
from pathlib import Path

def generate_html(demo_data_file, output_html_file=None):
    """Generate HTML visualization from demo data"""
    # Load demo data
    with open(demo_data_file, 'r') as f:
        demo_data = json.load(f)
    
    # Load HTML template
    template_path = Path(__file__).parent.parent / "templates" / "unified_ip_viewer.html"
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Replace placeholder with actual demo data
    template_content = template_content.replace(
        'const demoData = DEMO_DATA_PLACEHOLDER;',
        f'const demoData = {json.dumps(demo_data, indent=2)};'
    )
    
    # Determine output file if not provided
    if output_html_file is None:
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_html_file = output_dir / f"unified_ip_demo_view.html"
    
    # Write output HTML
    with open(output_html_file, 'w') as f:
        f.write(template_content)
    
    print(f"HTML visualization generated at: {output_html_file}")
    return output_html_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate HTML visualization from demo data")
    parser.add_argument("demo_data_file", help="Path to the demo data JSON file")
    parser.add_argument("--output", help="Path to the output HTML file")
    args = parser.parse_args()
    
    generate_html(args.demo_data_file, args.output) 