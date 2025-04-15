#!/bin/bash

# Run Discogs Collection Crawler
# This script handles OAuth setup and runs the collection crawler

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check if pip packages are installed
if ! python -c "import requests requests_oauthlib" &> /dev/null; then
    echo "Installing required dependencies..."
    pip install requests requests_oauthlib
fi

# Check if config file exists
if [ ! -f "config.json" ]; then
    echo "Error: config.json not found. Please create a configuration file first."
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

# Get username from command line
if [ $# -eq 0 ]; then
    echo "Error: Please provide a username to crawl"
    echo "Usage: $0 <username> [--sort field] [--sort-order asc|desc]"
    exit 1
fi

USERNAME="$1"
shift

# Run the crawler
echo "Starting collection crawl for user: $USERNAME"
python collection_crawler.py --config config.json --username "$USERNAME" "$@"

# Check if crawl was successful
if [ $? -eq 0 ]; then
    echo "Collection crawl completed successfully!"
    echo "Results saved to: $(pwd)/output/"
    
    # Display summary if available
    SUMMARY_FILE=$(ls -t output/crawl_summary_${USERNAME}_*.md 2>/dev/null | head -n1)
    if [ -n "$SUMMARY_FILE" ]; then
        echo ""
        echo "========== CRAWL SUMMARY =========="
        cat "$SUMMARY_FILE"
        echo "=================================="
    fi
else
    echo "Collection crawl failed. Check discogs_collection.log for details."
fi 