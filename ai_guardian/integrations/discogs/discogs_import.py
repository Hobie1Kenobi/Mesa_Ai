#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path
import discogs_client
from datetime import datetime
from time import sleep
import logging
from discogs_auth import authenticate, load_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DiscogsImporter:
    def __init__(self):
        self.config = load_config()
        self.setup_client()
        self.setup_output_dir()
        
    def setup_client(self):
        tokens = authenticate()
        self.client = discogs_client.Client(
            self.config['discogs']['user_agent'],
            user_token=tokens['token']
        )
        
    def setup_output_dir(self):
        output_dir = Path(self.config['output_directory'])
        output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir
        
    def search_releases(self, params):
        try:
            results = self.client.search(**params)
            sleep(self.config['discogs']['throttle_seconds'])
            return results
        except Exception as e:
            logger.error(f"Search failed with params {params}: {str(e)}")
            return []
            
    def convert_to_rights_record(self, release):
        try:
            artists = [a.name for a in release.artists]
            record = {
                "workTitle": release.title,
                "artistParty": artists[0] if artists else "Unknown",
                "publisherParty": release.labels[0].name if release.labels else "Unknown",
                "rightsType": self.config['rights_mapping']['default_type'],
                "territory": self.config['rights_mapping']['default_territory'],
                "term": {
                    "startDate": release.year if release.year else datetime.now().year,
                    "endDate": None
                },
                "royaltyInfo": {
                    "percentage": self.config['rights_mapping']['default_percentage']
                },
                "identifiers": {
                    "discogs_id": release.id,
                    "discogs_uri": release.url
                }
            }
            return record
        except Exception as e:
            logger.error(f"Failed to convert release {release.id}: {str(e)}")
            return None

    def import_by_genre(self, genre):
        logger.info(f"Importing releases for genre: {genre}")
        params = {
            'type': 'release',
            'genre': genre
        }
        results = self.search_releases(params)
        records = []
        for r in results[:self.config['import_params']['limit_per_search']]:
            if record := self.convert_to_rights_record(r):
                records.append(record)
        return records

    def import_by_artist(self, artist):
        logger.info(f"Importing releases for artist: {artist}")
        params = {
            'type': 'release',
            'artist': artist
        }
        results = self.search_releases(params)
        records = []
        for r in results[:self.config['import_params']['limit_per_search']]:
            if record := self.convert_to_rights_record(r):
                records.append(record)
        return records

    def import_by_year(self, year):
        logger.info(f"Importing releases for year: {year}")
        params = {
            'type': 'release',
            'year': year
        }
        results = self.search_releases(params)
        records = []
        for r in results[:self.config['import_params']['limit_per_search']]:
            if record := self.convert_to_rights_record(r):
                records.append(record)
        return records

    def run_import(self):
        all_records = []
        
        # Import by genres
        for genre in self.config['import_params']['genres']:
            records = self.import_by_genre(genre)
            all_records.extend(records)
            
        # Import by artists
        for artist in self.config['import_params']['artists']:
            records = self.import_by_artist(artist)
            all_records.extend(records)
            
        # Import by years
        years = range(
            self.config['import_params']['year_range']['start'],
            self.config['import_params']['year_range']['end'] + 1
        )
        for year in years:
            records = self.import_by_year(year)
            all_records.extend(records)
            
        # Save records
        if all_records:
            output_file = self.output_dir / 'rights_records.json'
            with open(output_file, 'w') as f:
                json.dump(all_records, f, indent=2)
            logger.info(f"Saved {len(all_records)} rights records to {output_file}")
            
        # Generate import summary
        summary = f"""
# Import Summary
- Total rights records: {len(all_records)}
- Genres searched: {len(self.config['import_params']['genres'])}
- Artists searched: {len(self.config['import_params']['artists'])}
- Years searched: {self.config['import_params']['year_range']['end'] - self.config['import_params']['year_range']['start'] + 1}
- Date: {datetime.now().isoformat()}
"""
        summary_file = self.output_dir / 'import_summary.md'
        with open(summary_file, 'w') as f:
            f.write(summary)
        logger.info(f"Saved import summary to {summary_file}")
        
        return len(all_records)

if __name__ == '__main__':
    importer = DiscogsImporter()
    num_records = importer.run_import()
    sys.exit(0 if num_records > 0 else 1) 