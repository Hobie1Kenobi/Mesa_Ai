#!/usr/bin/env python3

import os
import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("discogs_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("discogs_collection")

class DiscogsCollectionCrawler:
    """Crawler for Discogs user collections"""
    
    BASE_URL = "https://api.discogs.com"
    
    def __init__(self, config_path: str):
        """Initialize with configuration file"""
        self.config = self._load_config(config_path)
        self.session = self._create_session()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.config["output"]["directory"], exist_ok=True)
        
        # Stats for crawling
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "folders_crawled": 0,
            "releases_crawled": 0,
            "start_time": datetime.now(),
            "end_time": None
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            raise
    
    def _create_session(self) -> requests.Session:
        """Create authenticated session"""
        session = requests.Session()
        
        try:
            # Add token authentication
            session.headers.update({
                "Authorization": f"Discogs token={self.config['discogs']['token']}",
                "User-Agent": self.config["discogs"].get("user_agent", "MESA_Rights_Vault/1.0")
            })
            
        except Exception as e:
            logger.error(f"Error setting up session: {str(e)}")
            raise
        
        return session
    
    def _rate_limit(self):
        """Implement rate limiting"""
        self.stats["total_requests"] += 1
        if self.stats["total_requests"] % self.config["discogs"]["throttle"]["calls_per_minute"] == 0:
            time.sleep(self.config["discogs"]["throttle"]["wait_time"])
        else:
            time.sleep(0.1)
    
    def get_collection_folders(self, username: str) -> List[Dict]:
        """Get all folders in a user's collection"""
        logger.info(f"Getting collection folders for user: {username}")
        
        try:
            self._rate_limit()
            url = f"{self.BASE_URL}/users/{username}/collection/folders"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            folders = data.get("folders", [])
            
            self.stats["successful_requests"] += 1
            self.stats["folders_crawled"] += len(folders)
            
            logger.info(f"Found {len(folders)} folders")
            return folders
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Error getting folders: {str(e)}")
            return []
    
    def get_folder_releases(self, username: str, folder_id: int, 
                          sort: str = None, sort_order: str = "asc", 
                          page: int = 1, per_page: int = 100) -> Tuple[List[Dict], bool]:
        """Get releases in a collection folder with pagination"""
        logger.info(f"Getting releases for folder {folder_id}, page {page}")
        
        params = {
            "page": page,
            "per_page": per_page
        }
        
        if sort:
            params["sort"] = sort
            params["sort_order"] = sort_order
        
        try:
            self._rate_limit()
            url = f"{self.BASE_URL}/users/{username}/collection/folders/{folder_id}/releases"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            releases = data.get("releases", [])
            
            # Check if there are more pages
            pagination = data.get("pagination", {})
            has_next = pagination.get("page", 0) < pagination.get("pages", 0)
            
            self.stats["successful_requests"] += 1
            self.stats["releases_crawled"] += len(releases)
            
            logger.info(f"Found {len(releases)} releases on page {page}")
            return releases, has_next
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Error getting releases: {str(e)}")
            return [], False
    
    def get_release_instances(self, username: str, release_id: int) -> List[Dict]:
        """Get all instances of a release in a user's collection"""
        logger.info(f"Getting instances for release {release_id}")
        
        try:
            self._rate_limit()
            url = f"{self.BASE_URL}/users/{username}/collection/releases/{release_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            instances = []
            
            # Extract instances from each folder
            for folder in data.get("folders", []):
                for instance in folder.get("instances", []):
                    instance["folder_id"] = folder["id"]
                    instance["folder_name"] = folder["name"]
                    instances.append(instance)
            
            self.stats["successful_requests"] += 1
            logger.info(f"Found {len(instances)} instances")
            return instances
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Error getting instances: {str(e)}")
            return []
    
    def get_collection_fields(self, username: str) -> List[Dict]:
        """Get custom collection fields"""
        logger.info(f"Getting custom fields for user: {username}")
        
        try:
            self._rate_limit()
            url = f"{self.BASE_URL}/users/{username}/collection/fields"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            fields = data.get("fields", [])
            
            self.stats["successful_requests"] += 1
            logger.info(f"Found {len(fields)} custom fields")
            return fields
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Error getting custom fields: {str(e)}")
            return []
    
    def get_collection_value(self, username: str) -> Optional[Dict]:
        """Get collection value statistics"""
        logger.info(f"Getting collection value for user: {username}")
        
        try:
            self._rate_limit()
            url = f"{self.BASE_URL}/users/{username}/collection/value"
            response = self.session.get(url)
            response.raise_for_status()
            
            self.stats["successful_requests"] += 1
            return response.json()
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Error getting collection value: {str(e)}")
            return None
    
    def verify_user(self, username: str) -> bool:
        """Verify that the user exists and has a public collection"""
        logger.info(f"Verifying user: {username}")
        
        try:
            self._rate_limit()
            url = f"{self.BASE_URL}/users/{username}"
            response = self.session.get(url)
            response.raise_for_status()
            
            # Check if user exists
            user_data = response.json()
            if not user_data.get("id"):
                logger.error(f"User {username} not found")
                return False
            
            # Check if collection is public
            if user_data.get("num_collection", 0) == 0:
                logger.error(f"User {username} has no public collection")
                return False
            
            logger.info(f"User {username} verified with {user_data.get('num_collection', 0)} items in collection")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying user: {str(e)}")
            return False
    
    def crawl_collection(self, username: str, sort: str = None, sort_order: str = "asc") -> Dict[str, Any]:
        """Crawl entire collection for a user"""
        logger.info(f"Starting collection crawl for user: {username}")
        
        # Initialize collection data
        collection_data = {
            "username": username,
            "crawl_date": datetime.now().isoformat(),
            "folders": [],
            "custom_fields": [],
            "collection_value": None,
            "total_releases": 0
        }
        
        try:
            # Verify user first
            if not self.verify_user(username):
                raise ValueError(f"Unable to access collection for user: {username}")
            
            # Get custom fields (only if authenticated as owner)
            try:
                collection_data["custom_fields"] = self.get_collection_fields(username)
            except Exception as e:
                logger.warning(f"Could not get custom fields (requires authentication as owner): {str(e)}")
            
            # Get collection value (only if authenticated as owner)
            try:
                collection_data["collection_value"] = self.get_collection_value(username)
            except Exception as e:
                logger.warning(f"Could not get collection value (requires authentication as owner): {str(e)}")
            
            # Get all folders
            folders = self.get_collection_folders(username)
            
            # If no folders found but user exists, try to access the "All" folder (ID 0)
            if not folders:
                logger.info("No folders found, trying to access 'All' folder")
                folders = [{
                    "id": 0,
                    "name": "All",
                    "count": 0  # We'll update this as we fetch releases
                }]
            
            # Crawl each folder
            for folder in folders:
                folder_data = {
                    "id": folder["id"],
                    "name": folder["name"],
                    "count": folder["count"],
                    "releases": []
                }
                
                # Get all releases in folder with pagination
                page = 1
                while True:
                    releases, has_next = self.get_folder_releases(
                        username, folder["id"], sort, sort_order, page
                    )
                    
                    # Update folder count for "All" folder
                    if folder["id"] == 0:
                        folder_data["count"] += len(releases)
                    
                    # Get instances for each release
                    for release in releases:
                        try:
                            release["instances"] = self.get_release_instances(
                                username, release["id"]
                            )
                        except Exception as e:
                            logger.warning(f"Could not get instances for release {release['id']}: {str(e)}")
                            release["instances"] = []
                        
                        folder_data["releases"].append(release)
                    
                    if not has_next:
                        break
                    page += 1
                
                collection_data["folders"].append(folder_data)
                collection_data["total_releases"] += len(folder_data["releases"])
            
            # Save collection data
            self._save_collection_data(username, collection_data)
            
            # Generate summary
            self._generate_crawl_summary(username, collection_data)
            
            return collection_data
            
        except Exception as e:
            logger.error(f"Error crawling collection: {str(e)}")
            # Still try to save what we got
            if collection_data["folders"] or collection_data["total_releases"] > 0:
                self._save_collection_data(username, collection_data)
                self._generate_crawl_summary(username, collection_data)
            raise
        finally:
            self.stats["end_time"] = datetime.now()
    
    def _save_collection_data(self, username: str, data: Dict):
        """Save collection data to file"""
        output_path = os.path.join(
            self.config["output"]["directory"],
            f"collection_{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        )
        
        try:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved collection data to {output_path}")
        except Exception as e:
            logger.error(f"Error saving collection data: {str(e)}")
    
    def _generate_crawl_summary(self, username: str, data: Dict):
        """Generate crawl summary"""
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        summary = f"""# Discogs Collection Crawl Summary

## Overview
- **Username**: {username}
- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Duration**: {duration.total_seconds() / 60:.2f} minutes
- **Total Folders**: {len(data["folders"])}
- **Total Releases**: {data["total_releases"]}
- **Custom Fields**: {len(data["custom_fields"])}

## API Statistics
- **Total Requests**: {self.stats["total_requests"]}
- **Successful Requests**: {self.stats["successful_requests"]}
- **Failed Requests**: {self.stats["failed_requests"]}

## Collection Value
"""
        
        if data["collection_value"]:
            value = data["collection_value"]
            summary += f"""- **Minimum**: ${value.get("minimum", 0):.2f}
- **Median**: ${value.get("median", 0):.2f}
- **Maximum**: ${value.get("maximum", 0):.2f}
"""
        
        summary += "\n## Folders\n"
        for folder in data["folders"]:
            summary += f"- **{folder['name']}**: {len(folder['releases'])} releases\n"
        
        if data["custom_fields"]:
            summary += "\n## Custom Fields\n"
            for field in data["custom_fields"]:
                summary += f"- **{field['name']}** ({field['type']})"
                if field.get("public"):
                    summary += " (public)"
                summary += "\n"
        
        summary_path = os.path.join(
            self.config["output"]["directory"],
            f"crawl_summary_{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
        )
        
        try:
            with open(summary_path, 'w') as f:
                f.write(summary)
            logger.info(f"Saved crawl summary to {summary_path}")
        except Exception as e:
            logger.error(f"Error saving crawl summary: {str(e)}")

def main():
    """Example usage of collection crawler"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Crawl Discogs user collections")
    parser.add_argument("--config", required=True, help="Path to configuration file")
    parser.add_argument("--username", required=True, help="Username to crawl")
    parser.add_argument("--sort", help="Sort releases by field")
    parser.add_argument("--sort-order", default="asc", choices=["asc", "desc"],
                       help="Sort order (asc or desc)")
    args = parser.parse_args()
    
    try:
        crawler = DiscogsCollectionCrawler(args.config)
        crawler.crawl_collection(args.username, args.sort, args.sort_order)
        return 0
    except Exception as e:
        logger.error(f"Crawl failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main()) 