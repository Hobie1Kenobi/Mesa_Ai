#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discogs API Connector for MESA Rights Vault
This module provides connectivity to the Discogs API for music metadata integration
with the MESA Rights Vault system, ensuring privacy-preserving data handling.
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.backends import default_backend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class DiscogsConnector:
    """
    Connector class for interacting with the Discogs API and integrating with 
    MESA Rights Vault's privacy-preserving architecture.
    """
    
    BASE_URL = "https://api.discogs.com"
    RATE_LIMIT_WINDOW = 60  # Discogs rate limits per minute
    
    def __init__(self, user_token: str = None, user_agent: str = None, config_path: str = None):
        """
        Initialize the Discogs connector with authentication details.
        
        Args:
            user_token: Personal access token for Discogs API
            user_agent: User-Agent string for API requests
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.user_token = user_token or self.config.get("user_token")
        self.user_agent = user_agent or self.config.get("user_agent", "MESARightsVault/1.0")
        self.request_count = 0
        self.last_request_time = time.time()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Authorization": f"Discogs token={self.user_token}",
            "Content-Type": "application/json"
        })
        
        # Load mapping configuration
        self.field_mappings = self.config.get("field_mappings", {})
        
        # Encryption key (in production, use a secure key management system)
        self._encryption_key = os.environ.get("MESA_ENCRYPTION_KEY", self.config.get("encryption_key")).encode()
        
        logger.info("Discogs connector initialized")
        
    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from a JSON file."""
        if not config_path:
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "discogs_config.json"
            )
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file not found at {config_path}. Using defaults.")
                return {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
        
    def _rate_limit_check(self):
        """Handle rate limiting for Discogs API."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # If we've made requests in the current window, check timing
        if self.request_count > 0 and elapsed < self.RATE_LIMIT_WINDOW:
            # If approaching rate limit, sleep
            if self.request_count >= 25:  # Discogs limit is 60 per minute for authenticated requests
                sleep_time = self.RATE_LIMIT_WINDOW - elapsed + 1
                logger.info(f"Rate limit approaching, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_request_time = time.time()
        # Reset counter if window has passed
        elif elapsed >= self.RATE_LIMIT_WINDOW:
            self.request_count = 0
            self.last_request_time = current_time
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None, data: Dict = None) -> Dict:
        """
        Make a request to the Discogs API with rate limiting handling.
        
        Args:
            endpoint: API endpoint to call
            method: HTTP method (GET, POST, etc.)
            params: URL parameters
            data: Request body for POST/PUT
            
        Returns:
            Dictionary containing the API response
        """
        self._rate_limit_check()
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        try:
            self.request_count += 1
            
            if method == "GET":
                response = self.session.get(url, params=params)
            elif method == "POST":
                response = self.session.post(url, params=params, json=data)
            elif method == "PUT":
                response = self.session.put(url, params=params, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            # Parse error response if available
            error_msg = "Unknown error"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("message", str(e))
            except:
                error_msg = str(e)
                
            raise Exception(f"Discogs API error: {error_msg}")

    def search_releases(self, query: str, params: Dict = None) -> Dict:
        """
        Search for releases in the Discogs database.
        
        Args:
            query: Search query string
            params: Additional search parameters
            
        Returns:
            Dictionary with search results
        """
        search_params = params or {}
        search_params["q"] = query
        search_params["type"] = "release"
        
        logger.info(f"Searching Discogs for releases matching: {query}")
        return self._make_request("/database/search", params=search_params)
    
    def get_release(self, release_id: int) -> Dict:
        """
        Get detailed information about a specific release.
        
        Args:
            release_id: Discogs release ID
            
        Returns:
            Dictionary with release information
        """
        logger.info(f"Fetching release data for ID: {release_id}")
        return self._make_request(f"/releases/{release_id}")
    
    def get_master(self, master_id: int) -> Dict:
        """
        Get master release information.
        
        Args:
            master_id: Discogs master release ID
            
        Returns:
            Dictionary with master release information
        """
        logger.info(f"Fetching master release data for ID: {master_id}")
        return self._make_request(f"/masters/{master_id}")
    
    def get_artist(self, artist_id: int) -> Dict:
        """
        Get artist information.
        
        Args:
            artist_id: Discogs artist ID
            
        Returns:
            Dictionary with artist information
        """
        logger.info(f"Fetching artist data for ID: {artist_id}")
        return self._make_request(f"/artists/{artist_id}")
    
    def get_label(self, label_id: int) -> Dict:
        """
        Get label information.
        
        Args:
            label_id: Discogs label ID
            
        Returns:
            Dictionary with label information
        """
        logger.info(f"Fetching label data for ID: {label_id}")
        return self._make_request(f"/labels/{label_id}")
    
    # Privacy-preserving methods
    
    def _encrypt_data(self, data: Union[Dict, List, str]) -> str:
        """Encrypt data for privacy-preserving storage."""
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
        elif not isinstance(data, str):
            data = str(data)
            
        # Convert to bytes
        data_bytes = data.encode('utf-8')
        
        # Create a padder
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data_bytes) + padder.finalize()
        
        # Generate a random IV
        iv = os.urandom(16)
        
        # Create the cipher
        cipher = Cipher(
            algorithms.AES(self._encryption_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine IV and encrypted data
        encrypted_package = iv + encrypted_data
        
        # Return as base64 string
        import base64
        return base64.b64encode(encrypted_package).decode('utf-8')
    
    def _decrypt_data(self, encrypted_data: str) -> Dict:
        """Decrypt data for processing."""
        import base64
        
        # Decode base64
        data_bytes = base64.b64decode(encrypted_data)
        
        # Extract IV and encrypted data
        iv = data_bytes[:16]
        ciphertext = data_bytes[16:]
        
        # Create the cipher
        cipher = Cipher(
            algorithms.AES(self._encryption_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()
        
        # Return as JSON
        return json.loads(decrypted_data.decode('utf-8'))
    
    def _hash_identifier(self, identifier: str) -> str:
        """Create secure hash of an identifier for reference."""
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(identifier.encode())
        return digest.finalize().hex()
    
    # MESA Rights Vault integration methods
    
    def map_to_mesa_schema(self, discogs_data: Dict, entity_type: str) -> Dict:
        """
        Map Discogs data to MESA Rights Vault schema.
        
        Args:
            discogs_data: Data from Discogs API
            entity_type: Type of entity (release, artist, etc.)
            
        Returns:
            Dictionary formatted according to MESA schema
        """
        mesa_data = {
            "source": "discogs",
            "source_id": str(discogs_data.get("id")),
            "import_date": datetime.now().isoformat(),
            "entity_type": entity_type
        }
        
        # Mapping based on entity type
        if entity_type == "release":
            mesa_data.update({
                "workTitle": discogs_data.get("title"),
                "releaseDate": discogs_data.get("released"),
                "artistParty": self._extract_artists(discogs_data),
                "publisherParty": self._extract_labels(discogs_data),
                "identifiers": self._extract_identifiers(discogs_data),
                "genres": discogs_data.get("genres", []),
                "styles": discogs_data.get("styles", []),
            })
        elif entity_type == "artist":
            mesa_data.update({
                "name": discogs_data.get("name"),
                "real_name": discogs_data.get("realname"),
                "profile": discogs_data.get("profile"),
                "urls": discogs_data.get("urls", []),
                "identifiers": [
                    {"type": "discogs_id", "value": str(discogs_data.get("id"))}
                ]
            })
        elif entity_type == "label":
            mesa_data.update({
                "name": discogs_data.get("name"),
                "profile": discogs_data.get("profile"),
                "contactInfo": discogs_data.get("contact_info"),
                "urls": discogs_data.get("urls", []),
                "identifiers": [
                    {"type": "discogs_id", "value": str(discogs_data.get("id"))}
                ]
            })
        
        return mesa_data
    
    def _extract_artists(self, release_data: Dict) -> List[Dict]:
        """Extract artist information from release data."""
        artists = []
        for artist in release_data.get("artists", []):
            artists.append({
                "name": artist.get("name"),
                "id": str(artist.get("id")),
                "role": "primary"
            })
        
        # Extract additional artists from credits if available
        for credit in release_data.get("extraartists", []):
            artists.append({
                "name": credit.get("name"),
                "id": str(credit.get("id")),
                "role": credit.get("role", "contributor")
            })
            
        return artists
    
    def _extract_labels(self, release_data: Dict) -> List[Dict]:
        """Extract label information from release data."""
        labels = []
        for label in release_data.get("labels", []):
            labels.append({
                "name": label.get("name"),
                "id": str(label.get("id")),
                "catno": label.get("catno")
            })
        return labels
    
    def _extract_identifiers(self, release_data: Dict) -> List[Dict]:
        """Extract standard identifiers from release data."""
        identifiers = []
        
        # Add Discogs ID
        identifiers.append({
            "type": "discogs_id",
            "value": str(release_data.get("id"))
        })
        
        # Add other identifiers from the identifiers array
        for id_obj in release_data.get("identifiers", []):
            id_type = id_obj.get("type", "").lower()
            id_value = id_obj.get("value")
            
            if id_type and id_value:
                # Map to standard identifier types
                if id_type in ["barcode", "upc"]:
                    id_type = "upc"
                elif id_type in ["matrix", "matrix / runout"]:
                    id_type = "matrix"
                    
                identifiers.append({
                    "type": id_type,
                    "value": id_value
                })
        
        return identifiers
    
    def find_rights_metadata(self, search_params: Dict) -> Dict:
        """
        Search for music rights metadata based on various parameters.
        
        Args:
            search_params: Dictionary with search parameters (title, artist, etc.)
            
        Returns:
            Dictionary with matching metadata and privacy-preserving references
        """
        # Build query string
        query_parts = []
        
        if "title" in search_params:
            query_parts.append(search_params["title"])
            
        if "artist" in search_params:
            query_parts.append(search_params["artist"])
            
        if "label" in search_params:
            query_parts.append(f"label:{search_params['label']}")
            
        if "year" in search_params:
            query_parts.append(f"year:{search_params['year']}")
            
        # Execute search
        query = " ".join(query_parts)
        search_results = self.search_releases(query)
        
        # Process results
        processed_results = []
        for result in search_results.get("results", [])[:5]:  # Limit to top 5 matches
            release_id = result.get("id")
            if release_id:
                # Get detailed release data
                release_data = self.get_release(release_id)
                
                # Map to MESA schema
                mesa_data = self.map_to_mesa_schema(release_data, "release")
                
                # Create privacy-preserving references
                reference_id = self._hash_identifier(f"discogs:release:{release_id}")
                
                # Encrypt full data for secure storage
                encrypted_data = self._encrypt_data(mesa_data)
                
                processed_results.append({
                    "reference_id": reference_id,
                    "match_score": self._calculate_match_score(mesa_data, search_params),
                    "preview": {
                        "title": mesa_data.get("workTitle"),
                        "artist": ", ".join([a.get("name", "") for a in mesa_data.get("artistParty", [])]),
                        "year": mesa_data.get("releaseDate", "")[:4] if mesa_data.get("releaseDate") else "",
                        "label": ", ".join([l.get("name", "") for l in mesa_data.get("publisherParty", [])])
                    },
                    "encrypted_data": encrypted_data
                })
        
        return {
            "query": query,
            "total_results": search_results.get("pagination", {}).get("items", 0),
            "results": processed_results
        }
    
    def _calculate_match_score(self, mesa_data: Dict, search_params: Dict) -> int:
        """Calculate a score representing how well the result matches search criteria."""
        score = 0
        
        # Title match (up to 50 points)
        if "title" in search_params and "workTitle" in mesa_data:
            title_search = search_params["title"].lower()
            title_result = mesa_data["workTitle"].lower()
            
            if title_search == title_result:
                score += 50
            elif title_search in title_result or title_result in title_search:
                score += 30
                
        # Artist match (up to 30 points)
        if "artist" in search_params and "artistParty" in mesa_data:
            artist_search = search_params["artist"].lower()
            for artist in mesa_data["artistParty"]:
                artist_name = artist.get("name", "").lower()
                if artist_search == artist_name:
                    score += 30
                    break
                elif artist_search in artist_name or artist_name in artist_search:
                    score += 15
                    break
                    
        # Year match (up to 10 points)
        if "year" in search_params and "releaseDate" in mesa_data:
            year_search = search_params["year"]
            year_result = mesa_data.get("releaseDate", "")[:4]
            if year_search == year_result:
                score += 10
                
        # Label match (up to 10 points)
        if "label" in search_params and "publisherParty" in mesa_data:
            label_search = search_params["label"].lower()
            for label in mesa_data["publisherParty"]:
                label_name = label.get("name", "").lower()
                if label_search == label_name:
                    score += 10
                    break
                elif label_search in label_name or label_name in label_search:
                    score += 5
                    break
                    
        return score
    
    def retrieve_rights_data(self, reference_id: str, decryption_key: str = None) -> Dict:
        """
        Retrieve and decrypt rights data using a reference ID.
        
        Args:
            reference_id: The privacy-preserving reference ID
            decryption_key: Optional key for decryption
            
        Returns:
            Decrypted rights data
        """
        # In a real implementation, this would retrieve the encrypted data from storage
        # For demonstration, we'll assume the encrypted data is passed in
        
        # This would be implemented to retrieve the data from a database or storage service
        raise NotImplementedError("This method should be implemented to retrieve stored encrypted data")

    def generate_zk_proof(self, reference_id: str, claim: Dict) -> Dict:
        """
        Generate a zero-knowledge proof for a rights claim.
        
        Args:
            reference_id: The privacy-preserving reference ID
            claim: The claim to prove (e.g., "is_owner", "has_rights_to_distribute")
            
        Returns:
            A ZK proof package
        """
        # This would integrate with the ZK proof system
        # For now, return a simulated proof
        return {
            "proof_id": f"zkp_{reference_id[:8]}_{int(time.time())}",
            "reference_id": reference_id,
            "claim_type": claim.get("type"),
            "timestamp": int(time.time()),
            "expires": int(time.time() + 86400),  # 24 hours
            "simulation": True  # Flag indicating this is a simulation
        }
    
    def verify_zk_proof(self, proof: Dict) -> bool:
        """
        Verify a zero-knowledge proof.
        
        Args:
            proof: The ZK proof package
            
        Returns:
            Boolean indicating validity
        """
        # This would integrate with the ZK proof verification system
        # For now, simply validate the structure
        required_fields = ["proof_id", "reference_id", "claim_type", "timestamp"]
        if all(field in proof for field in required_fields):
            # Check expiration
            if proof.get("expires", 0) > int(time.time()):
                return True
        return False
    
    def save_to_mesa_vault(self, mesa_data: Dict, privacy_settings: Dict = None) -> Dict:
        """
        Save Discogs data to MESA Rights Vault with privacy controls.
        
        Args:
            mesa_data: Data mapped to MESA schema
            privacy_settings: Privacy settings for the data
            
        Returns:
            Reference information for the stored data
        """
        # Default privacy settings if none provided
        if privacy_settings is None:
            privacy_settings = {
                "public_fields": ["workTitle", "releaseDate", "genres"],
                "private_fields": ["identifiers", "artistParty", "publisherParty"],
                "selective_disclosure": True
            }
            
        # Generate a unique ID for the right
        right_id = f"0x{os.urandom(20).hex()}"
        
        # Encrypt sensitive data based on privacy settings
        public_data = {}
        private_data = {}
        
        for field in mesa_data:
            if field in privacy_settings.get("public_fields", []):
                public_data[field] = mesa_data[field]
            else:
                private_data[field] = mesa_data[field]
                
        # Encrypt private data
        encrypted_private_data = self._encrypt_data(private_data)
        
        # Create reference hash
        reference_id = self._hash_identifier(f"mesa:right:{right_id}")
        
        # In a real implementation, this would store the data in the MESA Rights Vault
        # For demonstration, return the reference information
        return {
            "right_id": right_id,
            "reference_id": reference_id,
            "public_data": public_data,
            "encrypted_data": encrypted_private_data,
            "privacy_settings": privacy_settings
        }


def main():
    """Main function for testing the Discogs connector."""
    # Create connector with token from environment or config
    connector = DiscogsConnector()
    
    # Example search
    search_params = {
        "title": "Bohemian Rhapsody",
        "artist": "Queen"
    }
    
    try:
        results = connector.find_rights_metadata(search_params)
        print(f"Found {len(results['results'])} matches for '{results['query']}'")
        
        for i, result in enumerate(results['results']):
            print(f"\nMatch {i+1} (Score: {result['match_score']}/100):")
            print(f"Title: {result['preview']['title']}")
            print(f"Artist: {result['preview']['artist']}")
            print(f"Year: {result['preview']['year']}")
            print(f"Label: {result['preview']['label']}")
            print(f"Reference ID: {result['reference_id']}")
            
        # For the top result, demonstrate creating a rights reference
        if results['results']:
            top_result = results['results'][0]
            decrypted_data = connector._decrypt_data(top_result['encrypted_data'])
            
            # Save to MESA vault
            vault_reference = connector.save_to_mesa_vault(decrypted_data)
            print("\nSaved to MESA Rights Vault:")
            print(f"Right ID: {vault_reference['right_id']}")
            print(f"Reference ID: {vault_reference['reference_id']}")
            print("Public data fields:", list(vault_reference['public_data'].keys()))
            
            # Generate ZK proof
            proof = connector.generate_zk_proof(
                vault_reference['reference_id'], 
                {"type": "ownership"}
            )
            print("\nGenerated ZK proof:")
            print(f"Proof ID: {proof['proof_id']}")
            print(f"Claim type: {proof['claim_type']}")
            print(f"Valid: {connector.verify_zk_proof(proof)}")
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 