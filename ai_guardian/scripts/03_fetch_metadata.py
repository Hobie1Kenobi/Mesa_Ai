import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Set
import musicbrainzngs

# --- Configuration ---
# Set User-Agent for MusicBrainz API (replace with your app details)
musicbrainzngs.set_useragent(
    "MESA-AI-Guardian",
    "0.1",
    "mailto:contact@example.com" # Replace with a real contact email if possible
)

# Set logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directories
# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up three levels to get to the workspace root (scripts -> ai_guardian -> MESA_Base_Hackathon -> workspace)
WORKSPACE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..")) 
INPUT_DIR = os.path.join(WORKSPACE_ROOT, "output", "rights_analysis")
OUTPUT_DIR = os.path.join(WORKSPACE_ROOT, "output", "musicbrainz_analysis")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Rate limiting
API_DELAY = 1.1 # MusicBrainz requests 1 request per second max

class MetadataFetcher:
    def __init__(self, input_dir: str = INPUT_DIR, output_dir: str = OUTPUT_DIR):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_titles: Set[str] = set()
        self.processed_artist_mbids: Set[str] = set()
        # Initialize results structure properly
        self.results: Dict = {
            "summary": {},
            "titles_processed_count": 0,
            "artists_found": {}
        }
        logging.info(f"Input directory: {self.input_dir}")
        logging.info(f"Output directory: {self.output_dir}")

    def extract_titles(self, json_data: Dict) -> List[str]:
        """Extract titles from the works in the JSON data (borrowed from bmi_scraper)."""
        titles = []
        try:
            if isinstance(json_data, dict):
                # Handle both root level 'works' and nested structures
                works_list = json_data.get('works', [])
                if isinstance(works_list, list):
                    for work in works_list:
                        if isinstance(work, dict) and 'title' in work:
                            title = work['title'].strip()
                            # Basic validation for title quality
                            if (title and len(title) >= 3 and len(title) < 200 and
                                any(c.isalnum() for c in title) and
                                not title.isnumeric()):
                                titles.append(title)
                # Recursively check other parts of the dict
                for key, value in json_data.items():
                    if key != 'works' and isinstance(value, (dict, list)):
                         titles.extend(self.extract_titles(value))
            elif isinstance(json_data, list):
                for item in json_data:
                    if isinstance(item, (dict, list)):
                        titles.extend(self.extract_titles(item))
        except Exception as e:
            logging.error(f"Error extracting titles: {str(e)}")
        # Return unique titles from this specific data structure
        return list(set(titles))

    def read_json_files(self) -> List[str]:
        """Read all JSON files in the input directory and extract titles."""
        all_titles_set = set()
        try:
            if not os.path.isdir(self.input_dir):
                 logging.error(f"Input directory not found: {self.input_dir}")
                 return []
                 
            json_files = [f for f in os.listdir(self.input_dir) if f.endswith('.json')]
            total_files = len(json_files)
            logging.info(f"Found {total_files} JSON files to process in {self.input_dir}")
            if total_files == 0:
                return []

            for idx, filename in enumerate(json_files, 1):
                logging.debug(f"Processing file {idx}/{total_files}: {filename}")
                file_path = os.path.join(self.input_dir, filename)
                content = None # Initialize content to None
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        # Read cautiously - limit size
                        content = file.read(20_000_000) # Limit read size to 20MB
                        if len(content) >= 20_000_000:
                            logging.warning(f"File {filename} is very large, may be truncated.")
                        if not content or not content.strip():
                            logging.warning(f"File {filename} is empty or contains only whitespace.")
                            continue
                        
                        data = json.loads(content)
                        titles_in_file = self.extract_titles(data)
                        if titles_in_file:
                            all_titles_set.update(titles_in_file) # Add to set for uniqueness
                            logging.info(f"✓ File {idx}/{total_files}: Extracted {len(titles_in_file)} unique titles from {filename}")
                        else:
                            logging.info(f"- File {idx}/{total_files}: No valid titles found in {filename}")
                            
                except json.JSONDecodeError as je:
                    logging.error(f"JSON decode error in {filename} at position {je.pos}: {je.msg}")
                    # Log snippet near error if content was read
                    if content:
                         snippet_start = max(0, je.pos - 50)
                         snippet_end = min(len(content), je.pos + 50)
                         logging.error(f"Content near error: ...{content[snippet_start:snippet_end]}...")
                except MemoryError:
                     logging.error(f"MemoryError processing {filename}. Skipping this file.")
                except Exception as e:
                    logging.error(f"Error processing {filename}: {str(e)}", exc_info=True)

                # Optional brief pause to prevent high CPU during file reads
                if idx % 100 == 0:
                     time.sleep(0.1)

        except FileNotFoundError:
             logging.error(f"Input directory not found: {self.input_dir}")
             return []
        except Exception as e:
            logging.error(f"Failed to read JSON files: {e}", exc_info=True)
            return []

        unique_titles_list = list(all_titles_set)
        logging.info(f"Total unique valid titles collected: {len(unique_titles_list)}")
        return unique_titles_list

    def search_musicbrainz_for_title(self, title: str) -> List[Dict]:
        """Search MusicBrainz for artists associated with a title (via recordings or works)."""
        # Check cache first
        if title in self.processed_titles:
             logging.debug(f"Skipping already processed title: '{title}'")
             return []

        logging.info(f"-> Querying MusicBrainz for title: '{title}'")
        artists_found = []
        artist_mbids_found_this_search = set()

        try:
            # Search recordings (often more direct link to performing artists)
            # Use strict=True for potentially better title matching
            logging.debug(f"Searching recordings for '{title}'...")
            result = musicbrainzngs.search_recordings(query=title, limit=5, strict=True)
            time.sleep(API_DELAY)

            if result.get('recording-list'):
                logging.debug(f"Found {len(result['recording-list'])} recordings for '{title}'")
                for recording in result['recording-list']:
                    if 'artist-credit' in recording:
                        for credit in recording['artist-credit']:
                            # Handle both direct artist dict and {'artist': {...}} structure
                            artist_info = credit.get('artist', credit if isinstance(credit.get('id'), str) else None)
                            if artist_info:
                                mbid = artist_info.get('id')
                                name = artist_info.get('name')
                                if mbid and name and mbid not in artist_mbids_found_this_search:
                                    artists_found.append({'mbid': mbid, 'name': name, 'source': 'recording'})
                                    artist_mbids_found_this_search.add(mbid)
                                    logging.debug(f"   Found artist via recording: {name} ({mbid})")
            else:
                logging.debug(f"No recordings found for '{title}'. Trying works...")
                # Fallback: Search works (more likely to find writers)
                result_work = musicbrainzngs.search_works(query=title, limit=3, strict=True)
                time.sleep(API_DELAY)
                if result_work.get('work-list'):
                    logging.debug(f"Found {len(result_work['work-list'])} works for '{title}'")
                    for work in result_work['work-list']:
                        # Look for writer relationships
                        if 'artist-relation-list' in work:
                             for rel in work['artist-relation-list']:
                                  if rel.get('type') == 'writer' and 'artist' in rel:
                                      artist_info = rel['artist']
                                      mbid = artist_info.get('id')
                                      name = artist_info.get('name')
                                      if mbid and name and mbid not in artist_mbids_found_this_search:
                                          artists_found.append({'mbid': mbid, 'name': name, 'source': 'work (writer)'})
                                          artist_mbids_found_this_search.add(mbid)
                                          logging.debug(f"   Found artist via work (writer): {name} ({mbid})")
                else:
                    logging.debug(f"No works found for '{title}' either.")

        except musicbrainzngs.WebServiceError as exc:
            # Handle specific errors like rate limiting or server issues if needed
            logging.error(f"MusicBrainz API error for title '{title}': {exc}")
        except Exception as e:
            logging.error(f"Unexpected error searching title '{title}': {e}", exc_info=True)
        finally:
            # Add title to processed list regardless of outcome to avoid retries
            self.processed_titles.add(title)

        logging.info(f"<- Found {len(artists_found)} unique new artist(s) for title '{title}'")
        return artists_found # Return list of {'mbid': ..., 'name': ..., 'source': ...}

    def get_artist_details(self, artist_mbid: str, artist_name: str) -> Dict | None:
         """Fetch detailed information for a given artist MBID, returns None if skipped."""
         # Check cache first
         if artist_mbid in self.processed_artist_mbids:
              logging.debug(f"Skipping already processed artist MBID: {artist_mbid} ({artist_name})")
              return None # Indicate skip

         logging.info(f"-> Fetching details for artist: {artist_name} (MBID: {artist_mbid})")
         details = {
             'mbid': artist_mbid,
             'name': artist_name,
             'type': None,
             'area': None,
             'country': None,
             'disambiguation': None,
             'urls': [],
             'labels': []
         }
         try:
              # Define includes for relationships we want
              includes = ["url-rels", "label-rels", "area-rels"]
              artist_data = musicbrainzngs.get_artist_by_id(artist_mbid, includes=includes)['artist']
              time.sleep(API_DELAY)

              details['type'] = artist_data.get('type')
              details['disambiguation'] = artist_data.get('disambiguation')
              details['country'] = artist_data.get('country') # Usually 2-letter code

              # Extract Area info (more reliable than country sometimes)
              if 'area' in artist_data and artist_data['area']:
                   details['area'] = {
                       'name': artist_data['area'].get('name'),
                       'mbid': artist_data['area'].get('id')
                   }

              # Extract URLs with types
              if 'url-relation-list' in artist_data:
                   for rel in artist_data['url-relation-list']:
                        target_url = rel.get('target')
                        url_type = rel.get('type')
                        if target_url:
                             details['urls'].append({'type': url_type, 'url': target_url})

              # Extract Labels with MBIDs
              if 'label-relation-list' in artist_data:
                   for rel in artist_data['label-relation-list']:
                        if 'label' in rel and rel['label']:
                             label_name = rel['label'].get('name')
                             label_mbid = rel['label'].get('id')
                             if label_name:
                                 details['labels'].append({'name': label_name, 'mbid': label_mbid})

              logging.info(f"<- Successfully fetched details for {artist_name}")

         except musicbrainzngs.ResponseError as res_exc:
              # Handle 404 Not Found gracefully
              if hasattr(res_exc, 'cause') and hasattr(res_exc.cause, 'code') and res_exc.cause.code == 404:
                   logging.warning(f"Artist MBID not found (404): {artist_mbid} ({artist_name})")
              else:
                   logging.error(f"MusicBrainz Response Error for artist {artist_mbid}: {res_exc}")
              details = None # Indicate fetch failure
         except musicbrainzngs.WebServiceError as ws_exc:
              logging.error(f"MusicBrainz API Error for artist {artist_mbid}: {ws_exc}")
              details = None # Indicate fetch failure
         except Exception as e:
              logging.error(f"Unexpected error fetching details for artist {artist_mbid}: {e}", exc_info=True)
              details = None # Indicate fetch failure
         finally:
             # Add to processed list *after* attempt, even if failed, to avoid retrying indefinitely
             self.processed_artist_mbids.add(artist_mbid)
             
         return details

    def save_results(self, final_save=False):
        """Save the collected results to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Use a consistent filename for intermediate saves, overwrite it
        # Use a final timestamped name only at the very end
        filename_part = f"musicbrainz_analysis_intermediate.json"
        if final_save:
            filename_part = f"musicbrainz_analysis_FINAL_{timestamp}.json"
            
        filename = os.path.join(self.output_dir, filename_part)
        
        # Update summary info before saving
        self.results["summary"] = {
            "last_updated": datetime.now().isoformat(),
            "total_titles_processed": len(self.processed_titles),
            "total_artists_processed": len(self.processed_artist_mbids),
            "total_artists_with_details": len(self.results["artists_found"])
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            logging.info(f"Results ({'final' if final_save else 'intermediate'}) successfully saved to {filename}")
        except Exception as e:
            logging.error(f"Failed to save results to {filename}: {e}", exc_info=True)

    def run(self, limit_titles=None):
        """Main execution flow. Can limit titles for testing."""
        logging.info("--- Starting MusicBrainz Metadata Fetcher ---")
        titles_to_search = self.read_json_files()
        
        if not titles_to_search:
            logging.warning("No titles found to search. Exiting.")
            return

        if limit_titles and limit_titles < len(titles_to_search):
             logging.warning(f"Limiting search to the first {limit_titles} titles for testing.")
             titles_to_search = titles_to_search[:limit_titles]

        total_titles_to_process = len(titles_to_search)
        logging.info(f"Beginning search process for {total_titles_to_process} titles...")
        
        start_time = time.time()
        
        for i, title in enumerate(titles_to_search):
            current_time = time.time()
            elapsed = current_time - start_time
            avg_time_per_title = elapsed / (i + 1) if i > 0 else 0
            estimated_remaining = (total_titles_to_process - (i + 1)) * avg_time_per_title
            
            logging.info(f"--- Processing title {i+1}/{total_titles_to_process} --- Est. remaining: {time.strftime('%H:%M:%S', time.gmtime(estimated_remaining))}")

            # Search for artists associated with the title
            found_artists = self.search_musicbrainz_for_title(title)
            # Note: self.processed_titles is updated inside search_musicbrainz_for_title
            
            # Fetch details for newly found artists
            for artist in found_artists:
                artist_mbid = artist['mbid']
                artist_name = artist['name']
                
                # Get details only if we haven't processed this MBID before
                # The get_artist_details function handles the check internally now
                artist_details = self.get_artist_details(artist_mbid, artist_name)
                
                # If details were successfully fetched (not skipped and no error)
                if artist_details:
                    # Store the fetched details
                    self.results["artists_found"][artist_mbid] = artist_details
                    # Optionally, link this title to the artist's record
                    if 'associated_titles' not in self.results["artists_found"][artist_mbid]:
                        self.results["artists_found"][artist_mbid]['associated_titles'] = []
                    if title not in self.results["artists_found"][artist_mbid]['associated_titles']:
                         self.results["artists_found"][artist_mbid]['associated_titles'].append(title)
                # Else: artist was skipped or details fetch failed - already logged

            # Save progress periodically
            if (i + 1) % 50 == 0:
                logging.info(f"Processed {i+1} titles. Saving intermediate results...")
                self.save_results(final_save=False) 

        logging.info("--- Finished searching MusicBrainz for all titles ---")
        self.save_results(final_save=True) # Final save
        logging.info("MusicBrainz metadata fetching complete.")

# --- Main Execution ---
if __name__ == "__main__":
    # Example: Limit to first 100 titles for a quick test
    # fetcher = MetadataFetcher(input_dir=INPUT_DIR, output_dir=OUTPUT_DIR)
    # fetcher.run(limit_titles=100) 
    
    # Run for all titles
    fetcher = MetadataFetcher(input_dir=INPUT_DIR, output_dir=OUTPUT_DIR)
    fetcher.run()