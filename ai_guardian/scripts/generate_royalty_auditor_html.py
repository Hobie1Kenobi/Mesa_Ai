#!/usr/bin/env python3

import json
import argparse
import os
from pathlib import Path

def generate_html(report_file, output_html_file=None):
    """Generate HTML visualization for royalty auditor results"""
    # Load report data
    with open(report_file, 'r') as f:
        report_data = json.load(f)
    
    # Load HTML template
    template_path = Path(__file__).parent.parent / "templates" / "royalty_auditor_viewer.html"
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Replace placeholder with actual report data
    template_content = template_content.replace(
        'const reportData = REPORT_DATA_PLACEHOLDER;',
        f'const reportData = {json.dumps(report_data, indent=2)};'
    )
    
    # Determine output file if not provided
    if output_html_file is None:
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_html_file = output_dir / f"royalty_auditor_results.html"
    
    # Write output HTML
    with open(output_html_file, 'w') as f:
        f.write(template_content)
    
    print(f"HTML visualization generated at: {output_html_file}")
    return output_html_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate HTML visualization for royalty auditor results")
    parser.add_argument("report_file", help="Path to the royalty auditor report JSON file")
    parser.add_argument("--output", help="Path to the output HTML file")
    args = parser.parse_args()
    
    generate_html(args.report_file, args.output) 