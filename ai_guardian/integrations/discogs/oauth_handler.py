#!/usr/bin/env python3

import os
import time
import random
import string
import logging
import requests
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("discogs_oauth.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("discogs_oauth")

class DiscogsOAuth:
    """Handles OAuth authentication flow for Discogs API"""
    
    BASE_URL = "https://api.discogs.com"
    REQUEST_TOKEN_URL = f"{BASE_URL}/oauth/request_token"
    ACCESS_TOKEN_URL = f"{BASE_URL}/oauth/access_token"
    AUTHORIZE_URL = "https://discogs.com/oauth/authorize"
    
    def __init__(self, consumer_key: str, consumer_secret: str, user_agent: str):
        """Initialize with application credentials"""
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.user_agent = user_agent
        self.request_token = None
        self.request_token_secret = None
        self.access_token = None
        self.access_token_secret = None
    
    def _generate_nonce(self, length: int = 16) -> str:
        """Generate a random nonce string"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string"""
        return str(int(time.time()))
    
    def get_request_token(self, callback_url: str = "oob") -> Tuple[str, str]:
        """
        Get OAuth request token from Discogs
        
        Args:
            callback_url: OAuth callback URL (use "oob" for pin-based auth)
            
        Returns:
            Tuple of (oauth_token, oauth_token_secret)
        """
        # Prepare OAuth parameters
        oauth_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_nonce": self._generate_nonce(),
            "oauth_signature": f"{self.consumer_secret}&",
            "oauth_signature_method": "PLAINTEXT",
            "oauth_timestamp": self._get_timestamp(),
            "oauth_callback": callback_url
        }
        
        # Create Authorization header
        auth_header = "OAuth " + ", ".join(f'{k}="{v}"' for k, v in oauth_params.items())
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": auth_header,
            "User-Agent": self.user_agent
        }
        
        try:
            response = requests.post(self.REQUEST_TOKEN_URL, headers=headers)
            response.raise_for_status()
            
            # Parse response
            response_params = dict(param.split('=') for param in response.text.split('&'))
            
            self.request_token = response_params['oauth_token']
            self.request_token_secret = response_params['oauth_token_secret']
            
            logger.info("Successfully obtained request token")
            return self.request_token, self.request_token_secret
            
        except Exception as e:
            logger.error(f"Error getting request token: {str(e)}")
            raise
    
    def get_authorize_url(self) -> str:
        """Get the authorization URL for user to approve access"""
        if not self.request_token:
            raise ValueError("Must get request token first")
        
        params = {
            "oauth_token": self.request_token
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"
    
    def get_access_token(self, oauth_verifier: str) -> Tuple[str, str]:
        """
        Get OAuth access token using verifier from user
        
        Args:
            oauth_verifier: Verification code from user
            
        Returns:
            Tuple of (access_token, access_token_secret)
        """
        if not self.request_token or not self.request_token_secret:
            raise ValueError("Must get request token first")
        
        # Prepare OAuth parameters
        oauth_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_nonce": self._generate_nonce(),
            "oauth_token": self.request_token,
            "oauth_signature": f"{self.consumer_secret}&{self.request_token_secret}",
            "oauth_signature_method": "PLAINTEXT",
            "oauth_timestamp": self._get_timestamp(),
            "oauth_verifier": oauth_verifier
        }
        
        # Create Authorization header
        auth_header = "OAuth " + ", ".join(f'{k}="{v}"' for k, v in oauth_params.items())
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": auth_header,
            "User-Agent": self.user_agent
        }
        
        try:
            response = requests.post(self.ACCESS_TOKEN_URL, headers=headers)
            response.raise_for_status()
            
            # Parse response
            response_params = dict(param.split('=') for param in response.text.split('&'))
            
            self.access_token = response_params['oauth_token']
            self.access_token_secret = response_params['oauth_token_secret']
            
            logger.info("Successfully obtained access token")
            return self.access_token, self.access_token_secret
            
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            raise
    
    def save_tokens(self, filename: str = "discogs_tokens.json") -> None:
        """Save tokens to a file"""
        import json
        
        data = {
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret,
            "access_token": self.access_token,
            "access_token_secret": self.access_token_secret
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Tokens saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving tokens: {str(e)}")
            raise
    
    @classmethod
    def load_tokens(cls, filename: str = "discogs_tokens.json") -> Dict[str, str]:
        """Load tokens from a file"""
        import json
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            logger.info(f"Tokens loaded from {filename}")
            return data
        except Exception as e:
            logger.error(f"Error loading tokens: {str(e)}")
            raise

def main():
    """Example usage of DiscogsOAuth"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Authenticate with Discogs API")
    parser.add_argument("--consumer-key", required=True, help="Your Discogs consumer key")
    parser.add_argument("--consumer-secret", required=True, help="Your Discogs consumer secret")
    parser.add_argument("--user-agent", default="MESA_Rights_Vault/1.0", help="User agent string")
    args = parser.parse_args()
    
    # Create OAuth handler
    oauth = DiscogsOAuth(args.consumer_key, args.consumer_secret, args.user_agent)
    
    try:
        # Get request token
        request_token, request_token_secret = oauth.get_request_token()
        
        # Get authorization URL
        auth_url = oauth.get_authorize_url()
        print(f"\nPlease visit this URL to authorize the application:\n{auth_url}\n")
        
        # Get verifier from user
        verifier = input("Enter the verification code: ").strip()
        
        # Get access token
        access_token, access_token_secret = oauth.get_access_token(verifier)
        
        # Save tokens
        oauth.save_tokens()
        
        print("\nAuthentication successful! Tokens have been saved.")
        
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 