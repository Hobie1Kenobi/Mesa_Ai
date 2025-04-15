#!/bin/bash

# Run Discogs Import Script with OAuth Authentication
# This script handles OAuth setup and runs the Discogs importer

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check if pip packages are installed
if ! python -c "import requests" &> /dev/null; then
    echo "Installing required dependencies..."
    pip install requests
fi

# Check if config file exists
if [ ! -f "config.json" ]; then
    echo "Error: config.json not found. Please create a configuration file first."
    echo "Example configuration:"
    echo '{
        "discogs": {
            "oauth": {
                "consumer_key": "YOUR_CONSUMER_KEY",
                "consumer_secret": "YOUR_CONSUMER_SECRET",
                "tokens_file": "discogs_tokens.json"
            },
            "user_agent": "MESA_Rights_Vault/1.0",
            "throttle": {
                "calls_per_minute": 25,
                "wait_time": 2.5
            }
        },
        "output": {
            "directory": "output",
            "batch_size": 100
        },
        "import": {
            "genres": ["Rock", "Electronic", "Jazz"],
            "artists": ["Radiohead", "Aphex Twin"],
            "years": ["1990-1999", "2000-2010"]
        }
    }'
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p output

# Load OAuth credentials from config
CONSUMER_KEY=$(python -c "import json; print(json.load(open('config.json'))['discogs']['oauth']['consumer_key'])")
CONSUMER_SECRET=$(python -c "import json; print(json.load(open('config.json'))['discogs']['oauth']['consumer_secret'])")
TOKENS_FILE=$(python -c "import json; print(json.load(open('config.json'))['discogs']['oauth']['tokens_file'])")
USER_AGENT=$(python -c "import json; print(json.load(open('config.json'))['discogs']['user_agent'])")

# Check if we need to authenticate
if [ ! -f "$TOKENS_FILE" ]; then
    echo "No OAuth tokens found. Starting authentication process..."
    
    # Run OAuth authentication
    python oauth_handler.py \
        --consumer-key "$CONSUMER_KEY" \
        --consumer-secret "$CONSUMER_SECRET" \
        --user-agent "$USER_AGENT"
    
    if [ $? -ne 0 ]; then
        echo "OAuth authentication failed. Please try again."
        exit 1
    fi
fi

# Run the importer
echo "Starting Discogs import process..."
python discogs_import.py --config config.json

# Check if import was successful
if [ $? -eq 0 ]; then
    echo "Import completed successfully!"
    echo "Results saved to: $(pwd)/output/"
    
    # Display summary if available
    if [ -f "output/import_summary.md" ]; then
        echo ""
        echo "========== IMPORT SUMMARY =========="
        cat output/import_summary.md
        echo "==================================="
    fi
else
    echo "Import failed. Check discogs_import.log for details."
fi 