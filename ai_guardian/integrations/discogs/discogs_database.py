#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Discogs Database for MESA Rights Vault
This module provides a database interface for caching and storing Discogs data
for integration with the MESA Rights Vault AI agent.
"""

import os
import json
import time
import logging
import sqlite3
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class DiscogsDatabase:
    """
    Database interface for caching and storing Discogs data structured for 
    the MESA Rights Vault AI agent.
    """
    
    def __init__(self, db_path: str = None, schema_path: str = None):
        """
        Initialize the Discogs database interface.
        
        Args:
            db_path: Path to the SQLite database file
            schema_path: Path to the database schema definition
        """
        # Set default paths if not provided
        if not db_path:
            db_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "discogs_data.db"
            )
        
        if not schema_path:
            schema_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "discogs_schema.json"
            )
            
        self.db_path = db_path
        self.schema_path = schema_path
        
        # Load schema
        self.schema = self._load_schema()
        
        # Initialize database
        self._init_db()
        
        logger.info(f"Discogs database initialized at {db_path}")
    
    def _load_schema(self) -> Dict:
        """Load the database schema from file."""
        try:
            if os.path.exists(self.schema_path):
                with open(self.schema_path, "r") as f:
                    return json.load(f)
            else:
                logger.warning(f"Schema file not found at {self.schema_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading schema: {e}")
            return {}
    
    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS releases (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                released TEXT,
                country TEXT,
                master_id INTEGER,
                data TEXT NOT NULL,
                imported_at TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS artists (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                realname TEXT,
                data TEXT NOT NULL,
                imported_at TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS labels (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                data TEXT NOT NULL,
                imported_at TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS release_artists (
                release_id INTEGER NOT NULL,
                artist_id INTEGER NOT NULL,
                role TEXT,
                PRIMARY KEY (release_id, artist_id, role),
                FOREIGN KEY (release_id) REFERENCES releases (id),
                FOREIGN KEY (artist_id) REFERENCES artists (id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS release_labels (
                release_id INTEGER NOT NULL,
                label_id INTEGER NOT NULL,
                catno TEXT,
                PRIMARY KEY (release_id, label_id, catno),
                FOREIGN KEY (release_id) REFERENCES releases (id),
                FOREIGN KEY (label_id) REFERENCES labels (id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS identifiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                release_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                value TEXT NOT NULL,
                FOREIGN KEY (release_id) REFERENCES releases (id),
                UNIQUE(release_id, type, value)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                release_id INTEGER NOT NULL,
                position TEXT,
                title TEXT NOT NULL,
                duration TEXT,
                data TEXT,
                FOREIGN KEY (release_id) REFERENCES releases (id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS mesa_rights (
                id TEXT PRIMARY KEY,
                discogs_release_id INTEGER,
                reference_id TEXT NOT NULL,
                public_data TEXT,
                encrypted_data TEXT NOT NULL,
                privacy_settings TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (discogs_release_id) REFERENCES releases (id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_agent_cache (
                query_hash TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                result TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                expiration TEXT NOT NULL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                params TEXT,
                response_code INTEGER,
                timestamp TEXT NOT NULL
            )
            ''')
            
            # Create indices for faster searches
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_releases_title ON releases (title)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_artists_name ON artists (name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_labels_name ON labels (name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_identifiers_value ON identifiers (value)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mesa_rights_reference ON mesa_rights (reference_id)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def save_release(self, release_data: Dict) -> int:
        """
        Save a Discogs release to the database.
        
        Args:
            release_data: Complete release data from Discogs API
            
        Returns:
            The release ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            release_id = release_data.get("id")
            if not release_id:
                raise ValueError("Release data must include an ID")
            
            # Check if release already exists
            cursor.execute("SELECT id FROM releases WHERE id = ?", (release_id,))
            exists = cursor.fetchone()
            
            timestamp = datetime.now().isoformat()
            
            # Format data for insertion
            release_json = json.dumps(release_data)
            title = release_data.get("title", "")
            released = release_data.get("released", "")
            country = release_data.get("country", "")
            master_id = release_data.get("master_id")
            
            if exists:
                # Update existing record
                cursor.execute('''
                UPDATE releases 
                SET title = ?, released = ?, country = ?, master_id = ?,
                    data = ?, last_updated = ?
                WHERE id = ?
                ''', (title, released, country, master_id, release_json, timestamp, release_id))
            else:
                # Insert new record
                cursor.execute('''
                INSERT INTO releases (id, title, released, country, master_id, data, imported_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (release_id, title, released, country, master_id, release_json, timestamp, timestamp))
            
            # Process artists
            if "artists" in release_data:
                for artist in release_data["artists"]:
                    artist_id = artist.get("id")
                    if artist_id:
                        # Save artist data if not already saved
                        self._save_artist_if_needed(cursor, artist_id, artist, timestamp)
                        
                        # Link artist to release
                        role = "primary"
                        try:
                            cursor.execute('''
                            INSERT OR REPLACE INTO release_artists (release_id, artist_id, role)
                            VALUES (?, ?, ?)
                            ''', (release_id, artist_id, role))
                        except sqlite3.IntegrityError:
                            pass
            
            # Process extraartists
            if "extraartists" in release_data:
                for artist in release_data["extraartists"]:
                    artist_id = artist.get("id")
                    if artist_id:
                        # Save artist data if not already saved
                        self._save_artist_if_needed(cursor, artist_id, artist, timestamp)
                        
                        # Link artist to release with role
                        role = artist.get("role", "contributor")
                        try:
                            cursor.execute('''
                            INSERT OR REPLACE INTO release_artists (release_id, artist_id, role)
                            VALUES (?, ?, ?)
                            ''', (release_id, artist_id, role))
                        except sqlite3.IntegrityError:
                            pass
            
            # Process labels
            if "labels" in release_data:
                for label in release_data["labels"]:
                    label_id = label.get("id")
                    if label_id:
                        # Save label data if not already saved
                        self._save_label_if_needed(cursor, label_id, label, timestamp)
                        
                        # Link label to release
                        catno = label.get("catno", "")
                        try:
                            cursor.execute('''
                            INSERT OR REPLACE INTO release_labels (release_id, label_id, catno)
                            VALUES (?, ?, ?)
                            ''', (release_id, label_id, catno))
                        except sqlite3.IntegrityError:
                            pass
            
            # Process identifiers
            if "identifiers" in release_data:
                for identifier in release_data["identifiers"]:
                    id_type = identifier.get("type", "").lower()
                    id_value = identifier.get("value", "")
                    
                    if id_type and id_value:
                        try:
                            cursor.execute('''
                            INSERT OR REPLACE INTO identifiers (release_id, type, value)
                            VALUES (?, ?, ?)
                            ''', (release_id, id_type, id_value))
                        except sqlite3.IntegrityError:
                            pass
            
            # Process tracks
            if "tracklist" in release_data:
                for track in release_data["tracklist"]:
                    position = track.get("position", "")
                    title = track.get("title", "")
                    duration = track.get("duration", "")
                    
                    if title:  # Only insert if there's a title
                        track_json = json.dumps(track)
                        try:
                            cursor.execute('''
                            INSERT INTO tracks (release_id, position, title, duration, data)
                            VALUES (?, ?, ?, ?, ?)
                            ''', (release_id, position, title, duration, track_json))
                        except sqlite3.IntegrityError:
                            pass
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved release {release_id}: {title}")
            return release_id
            
        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            logger.error(f"Error saving release: {e}")
            raise
    
    def _save_artist_if_needed(self, cursor, artist_id: int, artist_data: Dict, timestamp: str):
        """Save artist data if it doesn't already exist in the database."""
        cursor.execute("SELECT id FROM artists WHERE id = ?", (artist_id,))
        exists = cursor.fetchone()
        
        if not exists:
            # Only have basic info, insert what we have
            name = artist_data.get("name", "")
            realname = artist_data.get("realname", "")
            
            artist_json = json.dumps(artist_data)
            cursor.execute('''
            INSERT INTO artists (id, name, realname, data, imported_at, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (artist_id, name, realname, artist_json, timestamp, timestamp))
    
    def _save_label_if_needed(self, cursor, label_id: int, label_data: Dict, timestamp: str):
        """Save label data if it doesn't already exist in the database."""
        cursor.execute("SELECT id FROM labels WHERE id = ?", (label_id,))
        exists = cursor.fetchone()
        
        if not exists:
            # Only have basic info, insert what we have
            name = label_data.get("name", "")
            
            label_json = json.dumps(label_data)
            cursor.execute('''
            INSERT INTO labels (id, name, data, imported_at, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ''', (label_id, name, label_json, timestamp, timestamp))
    
    def save_mesa_right(self, right_data: Dict) -> str:
        """
        Save MESA rights data linked to a Discogs release.
        
        Args:
            right_data: MESA rights data
            
        Returns:
            The right ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            right_id = right_data.get("right_id")
            if not right_id:
                raise ValueError("Rights data must include a right_id")
            
            reference_id = right_data.get("reference_id")
            if not reference_id:
                raise ValueError("Rights data must include a reference_id")
            
            discogs_release_id = None
            if "discogs_release_id" in right_data:
                discogs_release_id = right_data["discogs_release_id"]
            
            # Check if right already exists
            cursor.execute("SELECT id FROM mesa_rights WHERE id = ?", (right_id,))
            exists = cursor.fetchone()
            
            timestamp = datetime.now().isoformat()
            
            # Format data for insertion
            public_data = json.dumps(right_data.get("public_data", {}))
            encrypted_data = right_data.get("encrypted_data", "")
            privacy_settings = json.dumps(right_data.get("privacy_settings", {}))
            
            if exists:
                # Update existing record
                cursor.execute('''
                UPDATE mesa_rights 
                SET discogs_release_id = ?, reference_id = ?, public_data = ?,
                    encrypted_data = ?, privacy_settings = ?, updated_at = ?
                WHERE id = ?
                ''', (discogs_release_id, reference_id, public_data, 
                      encrypted_data, privacy_settings, timestamp, right_id))
            else:
                # Insert new record
                cursor.execute('''
                INSERT INTO mesa_rights (id, discogs_release_id, reference_id, public_data,
                                       encrypted_data, privacy_settings, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (right_id, discogs_release_id, reference_id, public_data,
                      encrypted_data, privacy_settings, timestamp, timestamp))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved MESA right {right_id}")
            return right_id
            
        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            logger.error(f"Error saving MESA right: {e}")
            raise
    
    def get_release(self, release_id: int) -> Optional[Dict]:
        """
        Retrieve a release by ID.
        
        Args:
            release_id: Discogs release ID
            
        Returns:
            Release data or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT data FROM releases WHERE id = ?", (release_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return json.loads(row["data"])
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving release: {e}")
            if conn:
                conn.close()
            return None
    
    def get_artist(self, artist_id: int) -> Optional[Dict]:
        """
        Retrieve an artist by ID.
        
        Args:
            artist_id: Discogs artist ID
            
        Returns:
            Artist data or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT data FROM artists WHERE id = ?", (artist_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return json.loads(row["data"])
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving artist: {e}")
            if conn:
                conn.close()
            return None
    
    def get_label(self, label_id: int) -> Optional[Dict]:
        """
        Retrieve a label by ID.
        
        Args:
            label_id: Discogs label ID
            
        Returns:
            Label data or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT data FROM labels WHERE id = ?", (label_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return json.loads(row["data"])
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving label: {e}")
            if conn:
                conn.close()
            return None
    
    def get_mesa_right(self, right_id: str) -> Optional[Dict]:
        """
        Retrieve MESA rights data by ID.
        
        Args:
            right_id: MESA right ID
            
        Returns:
            Rights data or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, discogs_release_id, reference_id, public_data, 
                   encrypted_data, privacy_settings, created_at, updated_at
            FROM mesa_rights WHERE id = ?
            ''', (right_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "right_id": row["id"],
                    "discogs_release_id": row["discogs_release_id"],
                    "reference_id": row["reference_id"],
                    "public_data": json.loads(row["public_data"]),
                    "encrypted_data": row["encrypted_data"],
                    "privacy_settings": json.loads(row["privacy_settings"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving MESA right: {e}")
            if conn:
                conn.close()
            return None
    
    def search_releases(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for releases by title.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching releases
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_pattern = f"%{query}%"
            cursor.execute('''
            SELECT id, title, released, country 
            FROM releases 
            WHERE title LIKE ? 
            ORDER BY released DESC
            LIMIT ?
            ''', (search_pattern, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                result.append({
                    "id": row["id"],
                    "title": row["title"],
                    "released": row["released"],
                    "country": row["country"]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching releases: {e}")
            if conn:
                conn.close()
            return []
    
    def search_by_identifier(self, id_type: str, id_value: str) -> List[Dict]:
        """
        Search for releases by identifier (barcode, catalog number, etc.).
        
        Args:
            id_type: Type of identifier
            id_value: Identifier value
            
        Returns:
            List of matching releases
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT r.id, r.title, r.released, r.country 
            FROM releases r
            JOIN identifiers i ON r.id = i.release_id
            WHERE i.type = ? AND i.value = ?
            ''', (id_type.lower(), id_value))
            
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                result.append({
                    "id": row["id"],
                    "title": row["title"],
                    "released": row["released"],
                    "country": row["country"]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching by identifier: {e}")
            if conn:
                conn.close()
            return []
    
    def search_artists(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for artists by name.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching artists
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_pattern = f"%{query}%"
            cursor.execute('''
            SELECT id, name, realname
            FROM artists 
            WHERE name LIKE ? OR realname LIKE ?
            LIMIT ?
            ''', (search_pattern, search_pattern, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                result.append({
                    "id": row["id"],
                    "name": row["name"],
                    "realname": row["realname"]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching artists: {e}")
            if conn:
                conn.close()
            return []
    
    def get_releases_by_artist(self, artist_id: int, limit: int = 20) -> List[Dict]:
        """
        Get releases by a specific artist.
        
        Args:
            artist_id: Discogs artist ID
            limit: Maximum number of results
            
        Returns:
            List of releases
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT r.id, r.title, r.released, r.country, ra.role
            FROM releases r
            JOIN release_artists ra ON r.id = ra.release_id
            WHERE ra.artist_id = ?
            ORDER BY r.released DESC
            LIMIT ?
            ''', (artist_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                result.append({
                    "id": row["id"],
                    "title": row["title"],
                    "released": row["released"],
                    "country": row["country"],
                    "role": row["role"]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting releases by artist: {e}")
            if conn:
                conn.close()
            return []
    
    def log_api_request(self, endpoint: str, params: Dict = None, response_code: int = 200):
        """
        Log an API request for monitoring and rate limiting.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            response_code: HTTP response code
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            params_json = json.dumps(params) if params else None
            
            cursor.execute('''
            INSERT INTO api_requests (endpoint, params, response_code, timestamp)
            VALUES (?, ?, ?, ?)
            ''', (endpoint, params_json, response_code, timestamp))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging API request: {e}")
            if conn:
                conn.rollback()
                conn.close()
    
    def cache_ai_query(self, query: str, result: Dict, expiration_seconds: int = 86400):
        """
        Cache an AI agent query result for faster responses.
        
        Args:
            query: Original query string
            result: Query result
            expiration_seconds: Cache expiration in seconds
        """
        import hashlib
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create a hash of the query for efficient lookup
            query_hash = hashlib.sha256(query.encode()).hexdigest()
            
            timestamp = datetime.now().isoformat()
            expiration = datetime.now().timestamp() + expiration_seconds
            expiration_iso = datetime.fromtimestamp(expiration).isoformat()
            
            result_json = json.dumps(result)
            
            # Check if query already exists
            cursor.execute("SELECT query_hash FROM ai_agent_cache WHERE query_hash = ?", (query_hash,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing record
                cursor.execute('''
                UPDATE ai_agent_cache 
                SET result = ?, timestamp = ?, expiration = ?
                WHERE query_hash = ?
                ''', (result_json, timestamp, expiration_iso, query_hash))
            else:
                # Insert new record
                cursor.execute('''
                INSERT INTO ai_agent_cache (query_hash, query, result, timestamp, expiration)
                VALUES (?, ?, ?, ?, ?)
                ''', (query_hash, query, result_json, timestamp, expiration_iso))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error caching AI query: {e}")
            if conn:
                conn.rollback()
                conn.close()
    
    def get_cached_query(self, query: str) -> Optional[Dict]:
        """
        Retrieve a cached AI agent query result.
        
        Args:
            query: Original query string
            
        Returns:
            Cached result or None if not found or expired
        """
        import hashlib
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Create a hash of the query for efficient lookup
            query_hash = hashlib.sha256(query.encode()).hexdigest()
            
            cursor.execute('''
            SELECT result, expiration 
            FROM ai_agent_cache 
            WHERE query_hash = ?
            ''', (query_hash,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # Check if cache has expired
                expiration = datetime.fromisoformat(row["expiration"])
                if datetime.now() < expiration:
                    return json.loads(row["result"])
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached query: {e}")
            if conn:
                conn.close()
            return None
    
    def cleanup_expired_cache(self):
        """Remove expired entries from the cache."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
            DELETE FROM ai_agent_cache 
            WHERE expiration < ?
            ''', (now,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} expired cache entries")
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            if conn:
                conn.rollback()
                conn.close()
    
    def get_api_request_count(self, minutes: int = 60) -> int:
        """
        Get the number of API requests in the last X minutes.
        
        Args:
            minutes: Time window in minutes
            
        Returns:
            Number of requests
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate timestamp for X minutes ago
            time_ago = (datetime.now() - datetime.timedelta(minutes=minutes)).isoformat()
            
            cursor.execute('''
            SELECT COUNT(*) as count
            FROM api_requests
            WHERE timestamp > ?
            ''', (time_ago,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]
            return 0
            
        except Exception as e:
            logger.error(f"Error getting API request count: {e}")
            if conn:
                conn.close()
            return 0


def main():
    """Test the database implementation."""
    db = DiscogsDatabase()
    
    # Example release data for testing
    test_release = {
        "id": 123456,
        "title": "Test Album",
        "released": "2022",
        "country": "US",
        "master_id": 789012,
        "artists": [
            {"id": 111, "name": "Test Artist"}
        ],
        "labels": [
            {"id": 222, "name": "Test Label", "catno": "TL-123"}
        ],
        "identifiers": [
            {"type": "barcode", "value": "123456789012"}
        ],
        "tracklist": [
            {"position": "A1", "title": "Test Track 1", "duration": "3:45"},
            {"position": "A2", "title": "Test Track 2", "duration": "4:30"}
        ]
    }
    
    # Save test release
    release_id = db.save_release(test_release)
    print(f"Saved release: {release_id}")
    
    # Retrieve and verify
    retrieved = db.get_release(release_id)
    print(f"Retrieved: {retrieved['title']}")
    
    # Test search
    search_results = db.search_releases("Test")
    print(f"Found {len(search_results)} results")
    for result in search_results:
        print(f"- {result['title']} ({result['released']})")


if __name__ == "__main__":
    main() 