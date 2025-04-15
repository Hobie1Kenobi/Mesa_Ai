#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discogs Data Pull for MESA Rights Vault

This script pulls music metadata from the Discogs API and processes it into
the MESA Rights Vault format with appropriate privacy controls.

The script supports pulling data by:
- Genres
- Artists
- Years

Configuration is loaded from config.json and should include:
- discogs_token: Your Discogs API token
- genres: List of genres to pull data for
- artists: List of artists to pull data for
- years: List of years to pull data for
- batch_size: Number of items to pull per request
- max_items_per_category: Maximum items to pull per category
- output_directory: Directory to store the output data
- privacy_settings: Configuration for privacy controls

Usage:
    python data_pull.py
"""

import os
import json
import time
import logging
import random
import hashlib
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
import sys

# Add parent directory to path for imports from MESA Rights Vault
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

# Import MESA Rights Vault components
from ai_guardian.src.rights_guardian import RightsGuardian, MusicRight
from ai_guardian.scripts.privacy_layer import PrivacyLayer
from ai_guardian.scripts.zk_proofs import ZKProofSystem

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'discogs_pull.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('discogs_pull')

class DiscogsBulkDataPull:
    """Class for pulling bulk data from Discogs API and processing it into MESA Rights Vault format."""
    
    DISCOGS_API_BASE = "https://api.discogs.com"
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize with path to configuration file."""
        self.config_path = config_path
        self.config = self.load_config()
        self.token = self.config.get("discogs_token")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MESA_Rights_Vault_DataProcessor/1.0",
            "Authorization": f"Discogs token={self.token}"
        })
        
        # Initialize MESA Rights Vault components
        self.rights_guardian = RightsGuardian()
        self.privacy_layer = PrivacyLayer()
        self.zk_system = ZKProofSystem()
        
        # Create output directory if it doesn't exist
        self.output_dir = os.path.join(
            os.path.dirname(__file__), 
            self.config.get("output_directory", "../../../data/discogs_output")
        )
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Stats tracking
        self.stats = {
            "total_api_calls": 0,
            "total_releases_processed": 0,
            "total_rights_entries_created": 0,
            "genres_processed": {},
            "artists_processed": {},
            "years_processed": {},
            "errors": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading configuration: {e}")
            raise

    def pull_data(self):
        """Pull data based on configuration settings."""
        try:
            logger.info("Starting Discogs data pull")
            
            # Pull by genres if configured
            if self.config.get("genres"):
                self.pull_by_genres(self.config["genres"])
            
            # Pull by artists if configured
            if self.config.get("artists"):
                self.pull_by_artists(self.config["artists"])
            
            # Pull by years if configured
            if self.config.get("years"):
                self.pull_by_years(self.config["years"])
            
            # Save stats
            self.stats["end_time"] = datetime.now().isoformat()
            with open(os.path.join(self.output_dir, "pull_stats.json"), 'w') as f:
                json.dump(self.stats, f, indent=2)
            
            logger.info(f"Data pull complete. Processed {self.stats['total_releases_processed']} releases and created {self.stats['total_rights_entries_created']} rights entries.")
            
            return True
        except Exception as e:
            logger.error(f"Error in data pull: {e}")
            return False

    def pull_by_genres(self, genres: List[str]):
        """Pull releases by genres."""
        logger.info(f"Pulling data for {len(genres)} genres")
        
        for genre in genres:
            self.stats["genres_processed"][genre] = 0
            logger.info(f"Processing genre: {genre}")
            
            try:
                # Search for releases in this genre
                url = f"{self.DISCOGS_API_BASE}/database/search"
                params = {
                    "q": genre,
                    "type": "release",
                    "per_page": self.config.get("batch_size", 50)
                }
                
                releases = self._paginated_request(url, params, category="genre", category_value=genre)
                self._process_releases_batch(releases, metadata_category="genre", metadata_value=genre)
            
            except Exception as e:
                logger.error(f"Error processing genre {genre}: {e}")
                self.stats["errors"] += 1

    def pull_by_artists(self, artists: List[str]):
        """Pull releases by artists."""
        logger.info(f"Pulling data for {len(artists)} artists")
        
        for artist in artists:
            self.stats["artists_processed"][artist] = 0
            logger.info(f"Processing artist: {artist}")
            
            try:
                # Search for artist first to get ID
                url = f"{self.DISCOGS_API_BASE}/database/search"
                params = {
                    "q": artist,
                    "type": "artist",
                    "per_page": 1
                }
                
                response = self._make_api_request(url, params)
                
                if response and response.get("results") and len(response["results"]) > 0:
                    artist_id = response["results"][0].get("id")
                    
                    if artist_id:
                        # Get releases for this artist
                        url = f"{self.DISCOGS_API_BASE}/artists/{artist_id}/releases"
                        params = {
                            "per_page": self.config.get("batch_size", 50)
                        }
                        
                        releases = self._paginated_request(url, params, category="artist", category_value=artist)
                        self._process_releases_batch(releases, metadata_category="artist", metadata_value=artist)
            
            except Exception as e:
                logger.error(f"Error processing artist {artist}: {e}")
                self.stats["errors"] += 1

    def pull_by_years(self, years: List[str]):
        """Pull releases by years."""
        logger.info(f"Pulling data for {len(years)} years")
        
        for year in years:
            self.stats["years_processed"][year] = 0
            logger.info(f"Processing year: {year}")
            
            try:
                # Search for releases in this year
                url = f"{self.DISCOGS_API_BASE}/database/search"
                params = {
                    "year": year,
                    "type": "release",
                    "per_page": self.config.get("batch_size", 50)
                }
                
                releases = self._paginated_request(url, params, category="year", category_value=year)
                self._process_releases_batch(releases, metadata_category="year", metadata_value=year)
            
            except Exception as e:
                logger.error(f"Error processing year {year}: {e}")
                self.stats["errors"] += 1

    def _make_api_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a single API request to Discogs."""
        try:
            self.stats["total_api_calls"] += 1
            
            # Check if we need to rate limit
            if self.stats["total_api_calls"] > 1 and self.stats["total_api_calls"] % 25 == 0:
                logger.info("Rate limiting: sleeping for 60 seconds")
                time.sleep(60)
            else:
                # Small pause between requests
                time.sleep(random.uniform(1.0, 2.0))
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            logger.error(f"API request error: {e}")
            
            # Handle rate limiting
            if hasattr(e, "response") and e.response and e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                logger.info(f"Rate limited. Waiting for {retry_after} seconds")
                time.sleep(retry_after)
                return self._make_api_request(url, params)
            
            return {}

    def _paginated_request(self, url: str, params: Dict[str, Any], category: str, category_value: str) -> List[Dict[str, Any]]:
        """Make paginated requests to get all items up to max_items_per_category."""
        all_items = []
        page = 1
        max_items = self.config.get("max_items_per_category", 100)
        
        while len(all_items) < max_items:
            params["page"] = page
            response = self._make_api_request(url, params)
            
            # Extract results based on response structure
            if "results" in response:
                items = response.get("results", [])
            elif "releases" in response:
                items = response.get("releases", [])
            else:
                items = []
            
            if not items:
                break
                
            all_items.extend(items)
            
            # Update category stats
            if category == "genre":
                self.stats["genres_processed"][category_value] = len(all_items)
            elif category == "artist":
                self.stats["artists_processed"][category_value] = len(all_items)
            elif category == "year":
                self.stats["years_processed"][category_value] = len(all_items)
            
            # Check if there are more pages
            if not response.get("pagination", {}).get("urls", {}).get("next"):
                break
                
            page += 1
            
            # Check if we've reached our limit
            if len(all_items) >= max_items:
                all_items = all_items[:max_items]
                break
        
        logger.info(f"Retrieved {len(all_items)} items for {category}: {category_value}")
        return all_items

    def _process_releases_batch(self, releases: List[Dict[str, Any]], metadata_category: str, metadata_value: str):
        """Process a batch of releases and convert to rights entries."""
        logger.info(f"Processing batch of {len(releases)} releases")
        
        for release in releases:
            try:
                # Get full release details if we only have summary
                release_id = release.get("id")
                if release_id and "title" in release and "resource_url" in release:
                    full_release = self._make_api_request(release["resource_url"], {})
                    if full_release:
                        release = full_release
                
                # Convert to rights entry
                rights_entry = self._convert_to_rights_entry(release, metadata_category, metadata_value)
                
                if rights_entry:
                    # Apply privacy controls
                    self._apply_privacy_controls(rights_entry)
                    
                    self.stats["total_releases_processed"] += 1
                    self.stats["total_rights_entries_created"] += 1
            
            except Exception as e:
                logger.error(f"Error processing release: {e}")
                self.stats["errors"] += 1

    def _convert_to_rights_entry(self, release: Dict[str, Any], metadata_category: str, metadata_value: str) -> Dict[str, Any]:
        """Convert a Discogs release to a MESA Rights Vault entry."""
        try:
            # Extract basic information
            title = release.get("title", "Unknown Title")
            artist_name = release.get("artists_sort", "Unknown Artist")
            if isinstance(artist_name, list) and len(artist_name) > 0:
                artist_name = artist_name[0].get("name", "Unknown Artist")
            
            # Extract or generate a unique ID
            release_id = release.get("id", "")
            rights_id = hashlib.sha256(f"{release_id}_{title}_{artist_name}".encode()).hexdigest()[:16]
            
            # Extract additional metadata
            year = release.get("year", "")
            genres = release.get("genres", [])
            styles = release.get("styles", [])
            labels = []
            
            if "labels" in release and isinstance(release["labels"], list):
                labels = [label.get("name", "") for label in release["labels"] if "name" in label]
            
            # Create publisher party based on labels
            publisher = labels[0] if labels else "Unknown Publisher"
            
            # Generate dates
            current_year = datetime.now().year
            effective_date = f"{year}-01-01" if year and str(year).isdigit() else f"{current_year-10}-01-01"
            expiration_date = f"{int(year) + 70}-01-01" if year and str(year).isdigit() else f"{current_year + 60}-01-01"
            
            # Create rights entry
            rights_entry = {
                "rightId": rights_id,
                "workTitle": title,
                "artistParty": {
                    "name": artist_name,
                    "role": "Primary Artist",
                    "share": 50.0
                },
                "publisherParty": {
                    "name": publisher,
                    "role": "Publisher",
                    "share": 50.0
                },
                "rightsType": "Master Recording",
                "territory": "Worldwide",
                "term": f"{effective_date} to {expiration_date}",
                "royaltyInfo": {
                    "mechanicalRate": 0.091,
                    "streamingRate": 0.00348,
                    "syncRate": "negotiable"
                },
                "effectiveDate": effective_date,
                "expirationDate": expiration_date,
                "identifiers": {
                    "discogsId": str(release_id),
                    "catalogNumber": release.get("catalog_number", ""),
                    "barcode": release.get("barcode", "")
                },
                "metadata": {
                    "genres": genres,
                    "styles": styles,
                    "labels": labels,
                    "year": year,
                    "format": release.get("format", ""),
                    "country": release.get("country", ""),
                    "source": "Discogs",
                    "source_category": metadata_category,
                    "source_value": metadata_value
                }
            }
            
            return rights_entry
        
        except Exception as e:
            logger.error(f"Error converting release to rights entry: {e}")
            return None

    def _apply_privacy_controls(self, rights_entry: Dict[str, Any]):
        """Apply privacy controls to rights entry and save."""
        try:
            # Create a MusicRight object
            music_right = MusicRight(
                right_id=rights_entry["rightId"],
                title=rights_entry["workTitle"],
                rights_holder=rights_entry["artistParty"]["name"],
                rights_type=rights_entry["rightsType"],
                territory=rights_entry["territory"]
            )
            
            # Process with RightsGuardian
            processed_right = self.rights_guardian.process_rights_document(rights_entry)
            
            # Apply privacy settings from config
            privacy_settings = self.config.get("privacy_settings", {})
            
            # Determine which fields to encrypt
            public_fields = privacy_settings.get("public_fields", [])
            private_fields = privacy_settings.get("private_fields", [])
            
            # Create a version with only public fields for storage
            public_data = {k: rights_entry.get(k) for k in public_fields if k in rights_entry}
            
            # Create a version with private fields for encrypted storage
            private_data = {k: rights_entry.get(k) for k in private_fields if k in rights_entry}
            
            # Encrypt private data
            encrypted_data = self.privacy_layer.encrypt_rights_data(private_data)
            
            # Generate proof if enabled
            proof_data = None
            if privacy_settings.get("enable_zero_knowledge_proofs", False):
                proof_data = self.zk_system.create_ownership_proof_simulation(
                    rights_entry["rightId"], 
                    rights_entry["artistParty"]["name"]
                )
            
            # Combine for storage
            storage_entry = {
                "public": public_data,
                "encrypted": encrypted_data,
                "proofs": proof_data,
                "metadata": {
                    "creation_time": datetime.now().isoformat(),
                    "version": "1.0",
                    "privacy_level": privacy_settings.get("encryption_level", "standard")
                }
            }
            
            # Save to output directory
            output_path = os.path.join(self.output_dir, f"{rights_entry['rightId']}.json")
            with open(output_path, 'w') as f:
                json.dump(storage_entry, f, indent=2)
            
            logger.info(f"Saved rights entry with ID {rights_entry['rightId']}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error applying privacy controls: {e}")
            return False

if __name__ == "__main__":
    # Get configuration file path from command line or use default
    config_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "config.json")
    
    # Initialize and run data pull
    data_puller = DiscogsBulkDataPull(config_path)
    data_puller.pull_data() 