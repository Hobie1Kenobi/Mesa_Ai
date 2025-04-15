#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Agent Interface for Discogs Integration with MESA Rights Vault
This module provides the interface for the AI agent to interact with the 
Discogs database and MESA Rights Vault system.
"""

import os
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

from .discogs_connector import DiscogsConnector
from .discogs_database import DiscogsDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class DiscogsAIAgent:
    """
    AI Agent interface for retrieving and analyzing music rights data from 
    Discogs in coordination with the MESA Rights Vault.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the AI agent interface.
        
        Args:
            config_path: Path to configuration file
        """
        # Set default path if not provided
        if not config_path:
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "discogs_config.json"
            )
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.db = DiscogsDatabase()
        self.connector = DiscogsConnector(config_path=config_path)
        
        logger.info("Discogs AI agent interface initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from a JSON file."""
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
    
    def _hash_query(self, query: Dict) -> str:
        """Create a hash of a query for caching purposes."""
        query_str = json.dumps(query, sort_keys=True)
        return hashlib.sha256(query_str.encode()).hexdigest()
    
    def process_query(self, query: str, context: Dict = None) -> Dict:
        """
        Process a natural language query about music rights.
        
        Args:
            query: Natural language query string
            context: Additional context information
            
        Returns:
            Results and analysis
        """
        # Check cache first
        cached_result = self.db.get_cached_query(query)
        if cached_result:
            logger.info(f"Retrieved cached response for query: {query}")
            return {
                "response": cached_result,
                "source": "cache",
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract key entities from query
        entities = self._extract_entities(query)
        
        # Define query type
        query_type = self._determine_query_type(query, entities)
        
        # Process based on query type
        if query_type == "search":
            response = self._handle_search_query(entities)
        elif query_type == "rights_verification":
            response = self._handle_rights_verification(entities)
        elif query_type == "royalty_calculation":
            response = self._handle_royalty_calculation(entities, context)
        elif query_type == "metadata_lookup":
            response = self._handle_metadata_lookup(entities)
        else:
            response = {
                "success": False,
                "message": "Unable to determine query intent",
                "suggested_queries": [
                    "Who owns the rights to [song title]?",
                    "Find releases by [artist name]",
                    "What metadata is available for [song title]?"
                ]
            }
        
        # Cache the response
        self.db.cache_ai_query(query, response)
        
        return {
            "response": response,
            "source": "discogs_ai_agent",
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_entities(self, query: str) -> Dict:
        """
        Extract entities like artist names, song titles from a natural language query.
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary of extracted entities
        """
        # This would ideally use a more sophisticated NLP approach
        # For now, we'll use a simple keyword-based approach
        entities = {
            "artists": [],
            "titles": [],
            "years": [],
            "labels": [],
            "identifiers": []
        }
        
        # Look for common patterns in the query
        query_lower = query.lower()
        
        # Check for artist mentions
        if "by " in query_lower:
            parts = query_lower.split("by ")
            if len(parts) > 1:
                artist_part = parts[1].split("?")[0].split(",")[0].split(" in ")[0].strip()
                entities["artists"].append(artist_part)
        
        # Check for title mentions
        if '"' in query or "'" in query:
            import re
            # Find text in quotes
            quoted = re.findall(r'["\'](.*?)["\']', query)
            for title in quoted:
                entities["titles"].append(title)
        elif "called " in query_lower or "titled " in query_lower:
            for prefix in ["called ", "titled "]:
                if prefix in query_lower:
                    parts = query_lower.split(prefix)
                    if len(parts) > 1:
                        title_part = parts[1].split("?")[0].split(",")[0].split(" by ")[0].strip()
                        entities["titles"].append(title_part)
        
        # Check for years
        import re
        years = re.findall(r'\b(19|20)\d{2}\b', query)
        entities["years"].extend(years)
        
        # Check for label mentions
        if "on " in query_lower and " label" in query_lower:
            parts = query_lower.split("on ")
            if len(parts) > 1:
                label_part = parts[1].split("label")[0].strip()
                entities["labels"].append(label_part)
        
        # Check for identifiers like barcodes, ISRCs
        if "barcode" in query_lower:
            parts = query_lower.split("barcode")
            if len(parts) > 1:
                barcode_part = parts[1].strip().split()[0].strip()
                entities["identifiers"].append({"type": "barcode", "value": barcode_part})
        
        if "isrc" in query_lower:
            parts = query_lower.split("isrc")
            if len(parts) > 1:
                isrc_part = parts[1].strip().split()[0].strip()
                entities["identifiers"].append({"type": "isrc", "value": isrc_part})
        
        return entities
    
    def _determine_query_type(self, query: str, entities: Dict) -> str:
        """
        Determine the type of query being asked.
        
        Args:
            query: Natural language query string
            entities: Extracted entities
            
        Returns:
            Query type string
        """
        query_lower = query.lower()
        
        # Rights verification
        if any(term in query_lower for term in ["who owns", "rights", "rightsholder", "copyright"]):
            return "rights_verification"
        
        # Royalty calculation
        if any(term in query_lower for term in ["royalty", "royalties", "payment", "percentage", "earnings"]):
            return "royalty_calculation"
        
        # Metadata lookup
        if any(term in query_lower for term in ["metadata", "information about", "details", "tell me about"]):
            return "metadata_lookup"
        
        # Default to search if entities were found
        if any(entities[key] for key in entities):
            return "search"
        
        return "unknown"
    
    def _handle_search_query(self, entities: Dict) -> Dict:
        """
        Handle a search-type query by searching the Discogs database.
        
        Args:
            entities: Extracted entities
            
        Returns:
            Search results
        """
        results = []
        
        # Check for identifiers first (most specific)
        if entities["identifiers"]:
            for identifier in entities["identifiers"]:
                db_results = self.db.search_by_identifier(identifier["type"], identifier["value"])
                if db_results:
                    results.extend(db_results)
                else:
                    # Try API if not in database
                    search_params = {"type": identifier["type"], "value": identifier["value"]}
                    api_results = self.connector.find_rights_metadata(search_params)
                    for result in api_results.get("results", []):
                        release_id = self._extract_release_id_from_reference(result["reference_id"])
                        if release_id:
                            # Store in database for future queries
                            decrypted_data = self.connector._decrypt_data(result["encrypted_data"])
                            discogs_data = self._convert_mesa_to_discogs(decrypted_data)
                            self.db.save_release(discogs_data)
                            
                            # Add to results
                            results.append({
                                "id": release_id,
                                "title": result["preview"]["title"],
                                "artist": result["preview"]["artist"],
                                "year": result["preview"]["year"],
                                "label": result["preview"]["label"],
                                "score": result["match_score"]
                            })
            
            return {
                "success": True,
                "query_type": "identifier_search",
                "result_count": len(results),
                "results": results[:10]  # Limit to top 10
            }
        
        # Search by artist and title
        if entities["titles"] or entities["artists"]:
            search_params = {}
            
            if entities["titles"]:
                search_params["title"] = entities["titles"][0]
            
            if entities["artists"]:
                search_params["artist"] = entities["artists"][0]
            
            if entities["years"]:
                search_params["year"] = entities["years"][0]
            
            if entities["labels"]:
                search_params["label"] = entities["labels"][0]
            
            # Try database first
            db_results = []
            if "title" in search_params:
                db_results = self.db.search_releases(search_params["title"])
            
            if not db_results and "artist" in search_params:
                artist_results = self.db.search_artists(search_params["artist"])
                for artist in artist_results:
                    releases = self.db.get_releases_by_artist(artist["id"])
                    db_results.extend(releases)
            
            if db_results:
                results.extend(db_results)
            else:
                # Try API if not in database
                api_results = self.connector.find_rights_metadata(search_params)
                for result in api_results.get("results", []):
                    release_id = self._extract_release_id_from_reference(result["reference_id"])
                    if release_id:
                        # Add to results
                        results.append({
                            "id": release_id,
                            "title": result["preview"]["title"],
                            "artist": result["preview"]["artist"],
                            "year": result["preview"]["year"],
                            "label": result["preview"]["label"],
                            "score": result["match_score"]
                        })
            
            return {
                "success": True,
                "query_type": "metadata_search",
                "search_params": search_params,
                "result_count": len(results),
                "results": self._deduplicate_results(results)[:10]  # Limit to top 10
            }
        
        return {
            "success": False,
            "message": "Insufficient search criteria provided",
            "query_type": "search",
            "results": []
        }
    
    def _extract_release_id_from_reference(self, reference_id: str) -> Optional[int]:
        """Extract a Discogs release ID from a reference ID if possible."""
        # Reference IDs are hashes, but sometimes we can extract the original ID
        # This is just a placeholder for now
        return None
    
    def _convert_mesa_to_discogs(self, mesa_data: Dict) -> Dict:
        """Convert MESA format data back to Discogs format."""
        # This would be implemented to reverse the mapping done in the connector
        # For now, return a minimal structure
        return {
            "id": mesa_data.get("source_id"),
            "title": mesa_data.get("workTitle", ""),
            "released": mesa_data.get("releaseDate", ""),
            "country": mesa_data.get("territory", "")
        }
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate entries from search results."""
        seen_ids = set()
        deduplicated = []
        
        for result in results:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                deduplicated.append(result)
        
        return deduplicated
    
    def _handle_rights_verification(self, entities: Dict) -> Dict:
        """
        Handle a rights verification query.
        
        Args:
            entities: Extracted entities
            
        Returns:
            Rights verification result
        """
        if not (entities["titles"] or entities["artists"]):
            return {
                "success": False,
                "message": "Please specify a song title and/or artist to verify rights",
                "query_type": "rights_verification"
            }
        
        # First, search for the content
        search_result = self._handle_search_query(entities)
        
        if not search_result["success"] or search_result["result_count"] == 0:
            return {
                "success": False,
                "message": "Could not find the specified content to verify rights",
                "query_type": "rights_verification"
            }
        
        # For each potential match, check for rights information
        verified_rights = []
        
        for result in search_result["results"][:3]:  # Check top 3 matches
            release_id = result["id"]
            
            # Check if we have MESA rights information for this release
            mesa_rights = self._get_mesa_rights_for_release(release_id)
            
            if mesa_rights:
                for right in mesa_rights:
                    # Extract public information
                    public_info = {
                        "right_id": right["right_id"],
                        "reference_id": right["reference_id"],
                        "public_data": right["public_data"]
                    }
                    
                    # Generate a verification proof
                    proof = self.connector.generate_zk_proof(
                        right["reference_id"],
                        {"type": "ownership_verification"}
                    )
                    
                    verified_rights.append({
                        "release": {
                            "id": release_id,
                            "title": result["title"]
                        },
                        "rights_info": public_info,
                        "verification": {
                            "proof_id": proof["proof_id"],
                            "claim_type": proof["claim_type"],
                            "timestamp": proof["timestamp"],
                            "expires": proof["expires"]
                        }
                    })
        
        if not verified_rights:
            return {
                "success": True,
                "message": "Found potential matches, but no verified rights information is available",
                "query_type": "rights_verification",
                "potential_matches": search_result["results"][:5]
            }
        
        return {
            "success": True,
            "query_type": "rights_verification",
            "result_count": len(verified_rights),
            "results": verified_rights
        }
    
    def _get_mesa_rights_for_release(self, release_id: int) -> List[Dict]:
        """Get MESA rights information for a specific release."""
        # This would be implemented to query the database for rights
        # For now, return an empty list
        return []
    
    def _handle_royalty_calculation(self, entities: Dict, context: Dict = None) -> Dict:
        """
        Handle a royalty calculation query.
        
        Args:
            entities: Extracted entities
            context: Additional context information
            
        Returns:
            Royalty calculation result
        """
        if not (entities["titles"] or entities["artists"]):
            return {
                "success": False,
                "message": "Please specify a song title and/or artist for royalty calculation",
                "query_type": "royalty_calculation"
            }
        
        # Ensure we have context for calculation
        if not context or "calculation_parameters" not in context:
            return {
                "success": False,
                "message": "Insufficient context for royalty calculation. Please provide calculation parameters.",
                "query_type": "royalty_calculation",
                "required_parameters": [
                    "revenue_amount", 
                    "time_period", 
                    "territory"
                ]
            }
        
        # First, search for the content
        search_result = self._handle_search_query(entities)
        
        if not search_result["success"] or search_result["result_count"] == 0:
            return {
                "success": False,
                "message": "Could not find the specified content for royalty calculation",
                "query_type": "royalty_calculation"
            }
        
        # For demonstration purposes, return a simulated calculation
        calculation_parameters = context["calculation_parameters"]
        
        return {
            "success": True,
            "query_type": "royalty_calculation",
            "calculation_parameters": calculation_parameters,
            "content": {
                "title": search_result["results"][0]["title"],
                "id": search_result["results"][0]["id"]
            },
            "royalty_estimates": [
                {
                    "rightsholder": "Primary Artist",
                    "percentage": "50%",
                    "amount": calculation_parameters.get("revenue_amount", 1000) * 0.5
                },
                {
                    "rightsholder": "Songwriter",
                    "percentage": "25%",
                    "amount": calculation_parameters.get("revenue_amount", 1000) * 0.25
                },
                {
                    "rightsholder": "Publisher",
                    "percentage": "25%",
                    "amount": calculation_parameters.get("revenue_amount", 1000) * 0.25
                }
            ],
            "note": "This is a simulated calculation and would be based on actual rights data in a production environment"
        }
    
    def _handle_metadata_lookup(self, entities: Dict) -> Dict:
        """
        Handle a metadata lookup query.
        
        Args:
            entities: Extracted entities
            
        Returns:
            Metadata lookup result
        """
        if not (entities["titles"] or entities["artists"] or entities["identifiers"]):
            return {
                "success": False,
                "message": "Please specify a song title, artist, or identifier for metadata lookup",
                "query_type": "metadata_lookup"
            }
        
        # First, search for the content
        search_result = self._handle_search_query(entities)
        
        if not search_result["success"] or search_result["result_count"] == 0:
            return {
                "success": False,
                "message": "Could not find metadata for the specified content",
                "query_type": "metadata_lookup"
            }
        
        # For the top match, get complete metadata
        top_match = search_result["results"][0]
        release_id = top_match["id"]
        
        # Try to get from database first
        release_data = self.db.get_release(release_id)
        
        # If not in database, fetch from API
        if not release_data:
            try:
                release_data = self.connector.get_release(release_id)
                # Save to database for future queries
                if release_data:
                    self.db.save_release(release_data)
            except Exception as e:
                logger.error(f"Error fetching release data: {e}")
                release_data = None
        
        if not release_data:
            return {
                "success": False,
                "message": "Found a potential match, but could not retrieve detailed metadata",
                "query_type": "metadata_lookup",
                "basic_info": top_match
            }
        
        # Extract relevant metadata fields
        metadata = self._extract_metadata_fields(release_data)
        
        return {
            "success": True,
            "query_type": "metadata_lookup",
            "release_id": release_id,
            "metadata": metadata
        }
    
    def _extract_metadata_fields(self, release_data: Dict) -> Dict:
        """Extract important metadata fields from release data."""
        metadata = {
            "title": release_data.get("title", ""),
            "released": release_data.get("released", ""),
            "country": release_data.get("country", ""),
            "genres": release_data.get("genres", []),
            "styles": release_data.get("styles", [])
        }
        
        # Extract artists
        artists = []
        for artist in release_data.get("artists", []):
            artists.append({
                "id": artist.get("id"),
                "name": artist.get("name", ""),
                "role": "primary"
            })
        
        for artist in release_data.get("extraartists", []):
            artists.append({
                "id": artist.get("id"),
                "name": artist.get("name", ""),
                "role": artist.get("role", "contributor")
            })
        
        metadata["artists"] = artists
        
        # Extract labels
        labels = []
        for label in release_data.get("labels", []):
            labels.append({
                "id": label.get("id"),
                "name": label.get("name", ""),
                "catno": label.get("catno", "")
            })
        
        metadata["labels"] = labels
        
        # Extract identifiers
        identifiers = []
        for identifier in release_data.get("identifiers", []):
            identifiers.append({
                "type": identifier.get("type", ""),
                "value": identifier.get("value", "")
            })
        
        metadata["identifiers"] = identifiers
        
        # Extract tracklist
        tracks = []
        for track in release_data.get("tracklist", []):
            tracks.append({
                "position": track.get("position", ""),
                "title": track.get("title", ""),
                "duration": track.get("duration", "")
            })
        
        metadata["tracks"] = tracks
        
        return metadata
    
    def get_rights_for_entity(self, entity_type: str, entity_id: str) -> Dict:
        """
        Get rights information for a specific entity.
        
        Args:
            entity_type: Type of entity (release, artist, etc.)
            entity_id: Entity ID
            
        Returns:
            Rights information
        """
        if entity_type == "release":
            # Convert string ID to int if needed
            release_id = int(entity_id) if entity_id.isdigit() else entity_id
            
            # Check for MESA rights information
            mesa_rights = self._get_mesa_rights_for_release(release_id)
            
            if mesa_rights:
                return {
                    "success": True,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "rights_count": len(mesa_rights),
                    "rights": mesa_rights
                }
            
            # If no rights information, provide metadata for context
            release_data = self.db.get_release(release_id)
            
            if not release_data:
                try:
                    release_data = self.connector.get_release(release_id)
                    if release_data:
                        self.db.save_release(release_data)
                except Exception as e:
                    logger.error(f"Error fetching release data: {e}")
                    release_data = None
            
            if release_data:
                metadata = self._extract_metadata_fields(release_data)
                return {
                    "success": True,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "rights_count": 0,
                    "metadata": metadata,
                    "message": "No rights information is available, but metadata was found"
                }
        
        return {
            "success": False,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "message": "No rights information or metadata available for this entity"
        }
    
    def register_rights(self, entity_type: str, entity_id: str, rights_data: Dict) -> Dict:
        """
        Register new rights information for an entity.
        
        Args:
            entity_type: Type of entity (release, artist, etc.)
            entity_id: Entity ID
            rights_data: Rights information to register
            
        Returns:
            Registration result
        """
        if entity_type == "release":
            # Convert string ID to int if needed
            release_id = int(entity_id) if entity_id.isdigit() else entity_id
            
            # Verify the release exists
            release_data = self.db.get_release(release_id)
            
            if not release_data:
                try:
                    release_data = self.connector.get_release(release_id)
                    if release_data:
                        self.db.save_release(release_data)
                except Exception as e:
                    logger.error(f"Error fetching release data: {e}")
                    return {
                        "success": False,
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "message": f"Could not verify the entity exists: {str(e)}"
                    }
            
            if not release_data:
                return {
                    "success": False,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "message": "Could not verify the entity exists"
                }
            
            # Process and map release data to MESA schema
            mesa_data = self.connector.map_to_mesa_schema(release_data, "release")
            
            # Merge with provided rights data
            for key, value in rights_data.items():
                mesa_data[key] = value
            
            # Save to MESA vault
            privacy_settings = rights_data.get("privacy_settings")
            vault_reference = self.connector.save_to_mesa_vault(mesa_data, privacy_settings)
            
            # Save the reference in our database
            vault_reference["discogs_release_id"] = release_id
            right_id = self.db.save_mesa_right(vault_reference)
            
            return {
                "success": True,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "right_id": right_id,
                "reference_id": vault_reference["reference_id"],
                "message": "Rights successfully registered"
            }
        
        return {
            "success": False,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "message": f"Rights registration not supported for entity type: {entity_type}"
        }
    
    def verify_rights_claim(self, right_id: str, claim_type: str) -> Dict:
        """
        Verify a rights claim.
        
        Args:
            right_id: ID of the right
            claim_type: Type of claim to verify
            
        Returns:
            Verification result
        """
        # Get the rights data
        right_data = self.db.get_mesa_right(right_id)
        
        if not right_data:
            return {
                "success": False,
                "right_id": right_id,
                "claim_type": claim_type,
                "message": "Right not found"
            }
        
        # Generate a ZK proof for the claim
        proof = self.connector.generate_zk_proof(
            right_data["reference_id"],
            {"type": claim_type}
        )
        
        # Verify the proof
        is_verified = self.connector.verify_zk_proof(proof)
        
        if is_verified:
            return {
                "success": True,
                "right_id": right_id,
                "claim_type": claim_type,
                "verification": {
                    "proof_id": proof["proof_id"],
                    "verified": True,
                    "timestamp": proof["timestamp"],
                    "expires": proof["expires"]
                },
                "message": "Rights claim successfully verified"
            }
        
        return {
            "success": False,
            "right_id": right_id,
            "claim_type": claim_type,
            "verification": {
                "verified": False
            },
            "message": "Rights claim could not be verified"
        }


def main():
    """Test the AI agent implementation."""
    agent = DiscogsAIAgent()
    
    # Example query
    test_query = "Who owns the rights to 'Bohemian Rhapsody' by Queen?"
    
    # Process the query
    result = agent.process_query(test_query)
    
    # Print the result
    print(f"Query: {test_query}")
    print(f"Success: {result['response'].get('success', False)}")
    print(f"Message: {result['response'].get('message', '')}")
    print(f"Results: {result['response'].get('result_count', 0)}")
    
    # Print the first result if available
    if (result['response'].get('results') and 
        len(result['response']['results']) > 0):
        first_result = result['response']['results'][0]
        print("\nFirst result:")
        print(json.dumps(first_result, indent=2))


if __name__ == "__main__":
    main() 