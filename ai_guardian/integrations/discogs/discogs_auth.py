#!/usr/bin/env python3

import json
import os
import sys
import webbrowser
from time import sleep
import discogs_client
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path) as f:
        return json.load(f)

def save_tokens(tokens, tokens_file):
    with open(tokens_file, 'w') as f:
        json.dump(tokens, f, indent=2)

def authenticate():
    config = load_config()
    oauth_config = config['discogs']['oauth']
    tokens_file = Path(__file__).parent / oauth_config['tokens_file']
    
    if tokens_file.exists():
        print("Found existing tokens file")
        with open(tokens_file) as f:
            tokens = json.load(f)
            return tokens

    if not oauth_config['consumer_key'] or not oauth_config['consumer_secret']:
        print("Please set consumer_key and consumer_secret in config.json")
        sys.exit(1)

    d = discogs_client.Client(
        config['discogs']['user_agent'],
        consumer_key=oauth_config['consumer_key'],
        consumer_secret=oauth_config['consumer_secret']
    )

    # Get request token and authorization URL
    token, secret, url = d.get_authorize_url()
    
    print(f"Please visit this URL to authorize access: {url}")
    webbrowser.open(url)
    
    # Wait for user to authorize and get verifier
    verifier = input('Enter the verification code: ')

    # Exchange verifier for access token
    access_token, access_secret = d.get_access_token(verifier)

    tokens = {
        'token': access_token,
        'secret': access_secret
    }
    
    save_tokens(tokens, tokens_file)
    print(f"Tokens saved to {tokens_file}")
    
    return tokens

if __name__ == '__main__':
    authenticate() 