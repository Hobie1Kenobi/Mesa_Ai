#!/usr/bin/env python3
"""
MESA Rights Vault - Discogs Data Pull Script

This script pulls music release data from Discogs API and stores it in MESA Rights Vault
format with privacy controls implemented.

Features:
- Pulls data based on genres, artists, and/or years
- Implements rate limiting to respect Discogs API limits
- Applies privacy controls to the pulled data
- Saves rights entries in JSON format with privacy metadata
- Generates statistics about the data pull operation

Dependencies:
- requests: For API calls
- tqdm: For progress bars
- Proper Discogs API token in config file

Usage:
    python discogs_data_pull.py --config config.json

Configuration file (config.json) format:
{
    "discogs_token": "YOUR_DISCOGS_API_TOKEN",
    "genres": ["Electronic", "Rock", "Jazz"],
    "artists": ["Aphex Twin", "Radiohead"],
    "years": ["1990-1999", "2000-2010"],
    "batch_size": 100,
    "max_items_per_category": 1000,
    "output_dir": "discogs_data",
    "privacy_settings": {
        "enable_zk_proofs": true,
        "public_fields": ["rightId", "workTitle", "territory"],
        "private_fields": ["royaltyInfo", "publisherParty"],
        "selectively_disclosed_fields": {
            "artistParty": ["verifier1", "verifier2"],
            "effectiveDate": ["verifier1"]
        }
    }
}
"""

import os
import sys
import json
import time
import uuid
import random
import logging
import argparse
import datetime
import requests
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set
from tqdm import tqdm

# Add parent directory to path for importing privacy layer
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts"))

# Try to import the privacy layer
try:
    from privacy_layer import PrivacyLayer
    PRIVACY_AVAILABLE = True
except ImportError:
    PRIVACY_AVAILABLE = False
    print("Warning: Privacy layer not available. Data will be stored without privacy controls.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("discogs_data_pull.log")
    ]
)
logger = logging.getLogger("discogs_data_pull")

class DiscogsBulkDataPull:
    """Class to bulk pull data from Discogs API and store it in MESA Rights Vault format"""
    
    def __init__(self, config_path: str):
        """Initialize with config file path"""
        self.config = self._load_config(config_path)
        
        # Set up API parameters
        self.token = self.config["discogs_token"]
        self.base_url = "https://api.discogs.com"
        self.headers = {
            "User-Agent": "MESARightsVault/1.0",
            "Authorization": f"Discogs token={self.token}"
        }
        
        # Set up output directory
        self.output_dir = Path(self.config.get("output_dir", "discogs_data"))
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Set up counters for statistics
        self.stats = {
            "total_api_calls": 0,
            "total_releases_processed": 0,
            "total_rights_entries_created": 0,
            "errors": 0,
            "by_genre": {},
            "by_artist": {},
            "by_year": {},
            "start_time": datetime.datetime.now().isoformat(),
            "end_time": None
        }
        
        # Initialize privacy layer if available
        self.privacy_layer = PrivacyLayer() if PRIVACY_AVAILABLE else None
        
        logger.info(f"Initialized Discogs data puller with config from {config_path}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ["discogs_token"]
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Required field '{field}' missing from config")
            
            # Set defaults for optional fields
            config.setdefault("genres", [])
            config.setdefault("artists", [])
            config.setdefault("years", [])
            config.setdefault("batch_size", 100)
            config.setdefault("max_items_per_category", 1000)
            config.setdefault("output_dir", "discogs_data")
            config.setdefault("privacy_settings", {
                "enable_zk_proofs": True,
                "public_fields": ["rightId", "workTitle", "territory"],
                "private_fields": ["royaltyInfo", "publisherParty"],
                "selectively_disclosed_fields": {}
            })
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def pull_data(self) -> Dict[str, Any]:
        """Main method to pull data based on config"""
        logger.info("Starting data pull from Discogs API")
        
        try:
            # Pull data by genres
            if self.config["genres"]:
                logger.info(f"Pulling data for {len(self.config['genres'])} genres")
                self._pull_by_genres()
            
            # Pull data by artists
            if self.config["artists"]:
                logger.info(f"Pulling data for {len(self.config['artists'])} artists")
                self._pull_by_artists()
            
            # Pull data by years
            if self.config["years"]:
                logger.info(f"Pulling data for {len(self.config['years'])} year ranges")
                self._pull_by_years()
            
            # Save statistics
            self.stats["end_time"] = datetime.datetime.now().isoformat()
            stats_path = self.output_dir / "data_pull_stats.json"
            with open(stats_path, 'w') as f:
                json.dump(self.stats, f, indent=2)
            
            logger.info(f"Data pull complete. Processed {self.stats['total_releases_processed']} releases")
            logger.info(f"Created {self.stats['total_rights_entries_created']} rights entries")
            logger.info(f"Statistics saved to {stats_path}")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Error during data pull: {e}")
            raise
    
    def _pull_by_genres(self) -> None:
        """Pull releases by genres"""
        for genre in self.config["genres"]:
            logger.info(f"Pulling releases for genre: {genre}")
            
            self.stats["by_genre"][genre] = 0
            page = 1
            per_page = min(100, self.config["batch_size"])
            processed = 0
            
            try:
                with tqdm(total=self.config["max_items_per_category"], desc=f"Genre: {genre}") as pbar:
                    while processed < self.config["max_items_per_category"]:
                        # Search for releases with this genre
                        params = {
                            "type": "release",
                            "genre": genre,
                            "per_page": per_page,
                            "page": page
                        }
                        
                        response = self._make_api_request("/database/search", params)
                        if not response or "results" not in response:
                            break
                        
                        if len(response["results"]) == 0:
                            logger.info(f"No more results for genre: {genre}")
                            break
                        
                        # Process each release
                        for result in response["results"]:
                            if "id" in result:
                                self._process_release(result["id"], {"genre": genre})
                                processed += 1
                                self.stats["by_genre"][genre] += 1
                                pbar.update(1)
                            
                            if processed >= self.config["max_items_per_category"]:
                                break
                        
                        page += 1
                
                logger.info(f"Completed pulling for genre: {genre}. Processed {processed} releases")
                
            except Exception as e:
                logger.error(f"Error pulling data for genre {genre}: {e}")
                self.stats["errors"] += 1
    
    def _pull_by_artists(self) -> None:
        """Pull releases by artists"""
        for artist in self.config["artists"]:
            logger.info(f"Pulling releases for artist: {artist}")
            
            self.stats["by_artist"][artist] = 0
            page = 1
            per_page = min(100, self.config["batch_size"])
            processed = 0
            
            try:
                # First, search for the artist
                params = {
                    "type": "artist",
                    "q": artist,
                    "per_page": 5,
                    "page": 1
                }
                
                response = self._make_api_request("/database/search", params)
                if not response or "results" not in response or len(response["results"]) == 0:
                    logger.warning(f"Could not find artist: {artist}")
                    continue
                
                # Get artist ID from the first result (assuming it's the correct one)
                artist_id = response["results"][0]["id"]
                
                # Get releases by this artist
                with tqdm(total=self.config["max_items_per_category"], desc=f"Artist: {artist}") as pbar:
                    while processed < self.config["max_items_per_category"]:
                        releases_params = {
                            "sort": "year",
                            "sort_order": "desc",
                            "per_page": per_page,
                            "page": page
                        }
                        
                        releases_response = self._make_api_request(f"/artists/{artist_id}/releases", releases_params)
                        if not releases_response or "releases" not in releases_response:
                            break
                        
                        if len(releases_response["releases"]) == 0:
                            logger.info(f"No more releases for artist: {artist}")
                            break
                        
                        # Process each release
                        for release in releases_response["releases"]:
                            if "id" in release and release["type"] in ["master", "release"]:
                                self._process_release(release["id"], {"artist": artist})
                                processed += 1
                                self.stats["by_artist"][artist] += 1
                                pbar.update(1)
                            
                            if processed >= self.config["max_items_per_category"]:
                                break
                        
                        page += 1
                
                logger.info(f"Completed pulling for artist: {artist}. Processed {processed} releases")
                
            except Exception as e:
                logger.error(f"Error pulling data for artist {artist}: {e}")
                self.stats["errors"] += 1
    
    def _pull_by_years(self) -> None:
        """Pull releases by year ranges"""
        for year_range in self.config["years"]:
            try:
                # Parse year range (e.g., "1990-1999")
                start_year, end_year = map(int, year_range.split("-"))
                range_key = f"{start_year}-{end_year}"
                
                logger.info(f"Pulling releases for years: {range_key}")
                
                self.stats["by_year"][range_key] = 0
                processed = 0
                
                # Process each year in the range
                with tqdm(total=self.config["max_items_per_category"], desc=f"Years: {range_key}") as pbar:
                    for year in range(start_year, end_year + 1):
                        if processed >= self.config["max_items_per_category"]:
                            break
                        
                        page = 1
                        per_page = min(50, self.config["batch_size"])
                        
                        while processed < self.config["max_items_per_category"]:
                            # Search for releases in this year
                            params = {
                                "type": "release",
                                "year": year,
                                "per_page": per_page,
                                "page": page
                            }
                            
                            response = self._make_api_request("/database/search", params)
                            if not response or "results" not in response:
                                break
                            
                            if len(response["results"]) == 0:
                                break
                            
                            # Process each release
                            for result in response["results"]:
                                if "id" in result:
                                    self._process_release(result["id"], {"year": year})
                                    processed += 1
                                    self.stats["by_year"][range_key] += 1
                                    pbar.update(1)
                                
                                if processed >= self.config["max_items_per_category"]:
                                    break
                            
                            page += 1
                
                logger.info(f"Completed pulling for years {range_key}. Processed {processed} releases")
                
            except Exception as e:
                logger.error(f"Error pulling data for year range {year_range}: {e}")
                self.stats["errors"] += 1
    
    def _make_api_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make a request to the Discogs API with rate limiting"""
        url = f"{self.base_url}{endpoint}"
        self.stats["total_api_calls"] += 1
        
        try:
            # Add a small delay to respect rate limits (60 requests per minute)
            time.sleep(1.1)  # Just over 1 second to stay under the limit
            
            response = requests.get(url, headers=self.headers, params=params)
            
            # Check if we're hitting rate limits
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limit hit. Waiting for {retry_after} seconds")
                time.sleep(retry_after + 1)
                return self._make_api_request(endpoint, params)  # Retry
            
            # Check for other errors
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error making API request to {endpoint}: {e}")
            return None
    
    def _process_release(self, release_id: int, context: Dict[str, Any]) -> None:
        """Process a single release and create rights entries"""
        try:
            # Get release details
            release_data = self._make_api_request(f"/releases/{release_id}")
            if not release_data:
                return
            
            self.stats["total_releases_processed"] += 1
            
            # Extract relevant information for rights entries
            artists = [artist["name"] for artist in release_data.get("artists", [])]
            title = release_data.get("title", "Unknown Title")
            year = release_data.get("year", "Unknown")
            genres = release_data.get("genres", [])
            styles = release_data.get("styles", [])
            labels = [label["name"] for label in release_data.get("labels", [])]
            
            # Create rights entries
            for artist in artists:
                for label in labels or ["Unknown Label"]:
                    # Create a rights entry
                    right_entry = self._create_rights_entry(
                        title=title,
                        artist=artist,
                        publisher=label,
                        year=year,
                        genres=genres + styles,
                        context=context
                    )
                    
                    # Apply privacy controls if available
                    if PRIVACY_AVAILABLE and self.privacy_layer:
                        right_entry = self._apply_privacy_controls(right_entry)
                    
                    # Save the rights entry
                    right_id = right_entry["rightId"]
                    right_path = self.output_dir / f"right_{right_id}.json"
                    with open(right_path, 'w') as f:
                        json.dump(right_entry, f, indent=2)
                    
                    self.stats["total_rights_entries_created"] += 1
            
        except Exception as e:
            logger.error(f"Error processing release {release_id}: {e}")
            self.stats["errors"] += 1
    
    def _create_rights_entry(self, title: str, artist: str, publisher: str, 
                            year: Any, genres: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a rights entry in MESA Rights Vault format"""
        # Generate a unique ID for this right
        right_id = str(uuid.uuid4())
        
        # Get current date for effective date
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Generate an expiration date 5-70 years in the future
        years_ahead = random.randint(5, 70)
        expiration_date = (datetime.datetime.now() + datetime.timedelta(days=365 * years_ahead)).strftime("%Y-%m-%d")
        
        # Generate territories
        territories = random.choice([
            "Worldwide", "United States", "European Union", "Japan", 
            "United Kingdom", "Australia", "North America"
        ])
        
        # Generate rights type
        rights_type = random.choice([
            "Mechanical", "Performance", "Synchronization", "Print", 
            "Digital Distribution", "Streaming", "Master Recording"
        ])
        
        # Generate royalty information
        royalty_info = {
            "percentage": round(random.uniform(1.0, 25.0), 2),
            "paymentFrequency": random.choice(["Monthly", "Quarterly", "Biannually", "Annually"]),
            "minimumGuarantee": random.randint(0, 10000) if random.random() > 0.7 else 0
        }
        
        # Create identifiers (ISWC, ISRC, etc.)
        identifiers = {}
        
        # Simulate ISWC (International Standard Musical Work Code)
        if random.random() > 0.3:  # 70% chance to have ISWC
            identifiers["ISWC"] = f"T-{random.randint(100000, 999999)}-{random.randint(10, 99)}-{random.randint(1, 9)}"
        
        # Simulate ISRC (International Standard Recording Code)
        if random.random() > 0.2:  # 80% chance to have ISRC
            country_code = random.choice(["US", "GB", "JP", "DE", "FR", "CA", "AU"])
            year_code = str(year)[-2:] if isinstance(year, int) else str(random.randint(0, 99)).zfill(2)
            registrant = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
            designation = ''.join(random.choices('0123456789', k=5))
            identifiers["ISRC"] = f"{country_code}{year_code}{registrant}{designation}"
        
        # Create the rights entry
        rights_entry = {
            "rightId": right_id,
            "workTitle": title,
            "artistParty": {
                "name": artist,
                "role": "Performer",
                "contactInfo": {
                    "email": f"contact@{artist.lower().replace(' ', '')}.com"
                }
            },
            "publisherParty": {
                "name": publisher,
                "role": "Publisher",
                "contactInfo": {
                    "email": f"rights@{publisher.lower().replace(' ', '')}.com"
                }
            },
            "rightsType": rights_type,
            "territory": territories,
            "term": {
                "description": f"{years_ahead} years"
            },
            "royaltyInfo": royalty_info,
            "effectiveDate": current_date,
            "expirationDate": expiration_date,
            "identifiers": identifiers,
            "metadata": {
                "source": "Discogs",
                "genres": genres,
                "year": year,
                "context": context
            }
        }
        
        return rights_entry
    
    def _apply_privacy_controls(self, rights_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Apply privacy controls to a rights entry"""
        try:
            # Get privacy settings from config
            privacy_settings = self.config.get("privacy_settings", {})
            
            # Determine which fields are public and which are private
            public_fields = privacy_settings.get("public_fields", [])
            private_fields = privacy_settings.get("private_fields", [])
            
            # Extract data to encrypt
            private_data = {}
            for field in private_fields:
                if field in rights_entry:
                    private_data[field] = rights_entry[field]
            
            # If we have private data, encrypt it
            if private_data:
                encrypted_data, encryption_metadata = self.privacy_layer.encrypt_rights_data(private_data)
                
                # Add the privacy section to the rights entry
                rights_entry["_privacy"] = {
                    "encryptedData": encrypted_data,
                    "encryptionMetadata": encryption_metadata,
                    "availableProofs": []
                }
                
                # Generate selective disclosure proofs if enabled
                if privacy_settings.get("enable_zk_proofs", True):
                    selectively_disclosed_fields = privacy_settings.get("selectively_disclosed_fields", {})
                    
                    for field, allowed_verifiers in selectively_disclosed_fields.items():
                        if field in rights_entry:
                            # Create a selective disclosure proof
                            proof_data = {
                                "type": "selective_disclosure",
                                "field": field,
                                "allowedVerifiers": allowed_verifiers,
                                "proofParams": {
                                    "commitment": self._simulate_proof_commitment(field, rights_entry.get(field))
                                }
                            }
                            
                            rights_entry["_privacy"]["availableProofs"].append(proof_data)
                
                # Remove private fields from the main object since they're now encrypted
                for field in private_fields:
                    if field in rights_entry:
                        del rights_entry[field]
            
            return rights_entry
            
        except Exception as e:
            logger.error(f"Error applying privacy controls: {e}")
            return rights_entry  # Return without privacy if there's an error
    
    def _simulate_proof_commitment(self, field: str, value: Any) -> str:
        """Simulate a zero-knowledge proof commitment"""
        # In a real implementation, this would create an actual ZK proof
        # For this demo, we'll just create a placeholder hash
        value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        return f"commit_{field}_{hash(value_str) % 10000000:07d}"

def main():
    """Main function to run the script"""
    parser = argparse.ArgumentParser(description="Pull data from Discogs API and store in MESA Rights Vault format")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    args = parser.parse_args()
    
    try:
        # Create and run the data puller
        data_puller = DiscogsBulkDataPull(args.config)
        data_puller.pull_data()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 