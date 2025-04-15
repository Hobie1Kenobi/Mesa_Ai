import os
import json
import time
import random
from datetime import datetime
from typing import Dict, List
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

class BMIScraper:
    def __init__(self, input_dir: str = None, output_dir: str = None):
        # Get the workspace root directory
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        
        # Set default paths relative to workspace root
        if input_dir is None:
            input_dir = os.path.join(workspace_root, "output", "rights_analysis")
        if output_dir is None:
            output_dir = os.path.join(workspace_root, "output", "bmi_data")
            
        self.input_dir = input_dir
        self.output_dir = os.path.join(output_dir, datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Input directory: {self.input_dir}")
        print(f"Output directory: {self.output_dir}")
        
    def extract_titles(self, json_data: Dict) -> List[str]:
        """Extract titles from the works in the JSON data."""
        titles = []
        try:
            if isinstance(json_data, dict):
                if 'works' in json_data and isinstance(json_data['works'], list):
                    for work in json_data['works']:
                        if isinstance(work, dict) and 'title' in work:
                            # Clean and normalize the title
                            title = work['title'].strip()
                            # Validate the title
                            if (title and 
                                len(title) >= 3 and  # At least 3 characters
                                any(c.isalnum() for c in title) and  # Contains at least one alphanumeric character
                                not title.isnumeric()):  # Not just numbers
                                titles.append(title)
                            
                # Also check for nested works
                for value in json_data.values():
                    if isinstance(value, (dict, list)):
                        titles.extend(self.extract_titles(value))
            elif isinstance(json_data, list):
                for item in json_data:
                    if isinstance(item, (dict, list)):
                        titles.extend(self.extract_titles(item))
                        
        except Exception as e:
            print(f"Error extracting titles: {str(e)}")
            
        return list(set(titles))  # Remove duplicates

    def read_json_files(self) -> List[str]:
        """Read all JSON files in the input directory and extract titles."""
        all_titles = []
        json_files = [f for f in os.listdir(self.input_dir) if f.endswith('.json')]
        total_files = len(json_files)
        
        print(f"\nFound {total_files} JSON files to process")
        
        for idx, filename in enumerate(json_files, 1):
            print(f"\nProcessing file {idx}/{total_files}: {filename}")
            file_path = os.path.join(self.input_dir, filename)
            
            try:
                # First try to read the file contents with UTF-8
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        print(f"Reading {filename}...")
                        content = file.read(10_000_000)  # Read up to 10MB to prevent memory issues
                        if not content.strip():
                            print(f"Warning: {filename} is empty")
                            continue
                        
                        # Try to parse JSON
                        try:
                            print(f"Parsing JSON from {filename}...")
                            data = json.loads(content)
                            
                            # Extract titles from valid JSON
                            titles = self.extract_titles(data)
                            if titles:
                                all_titles.extend(titles)
                                print(f"✓ Extracted {len(titles)} titles from {filename}")
                            else:
                                print(f"No titles found in {filename}")
                            
                        except json.JSONDecodeError as je:
                            print(f"JSON decode error in {filename} at position {je.pos}: {je.msg}")
                            print(f"Content near error: {content[max(0, je.pos-50):je.pos+50]}")
                            continue
                            
                except UnicodeDecodeError:
                    # Try with different encodings if UTF-8 fails
                    for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            with open(file_path, 'r', encoding=encoding) as file:
                                content = file.read(10_000_000)  # Read up to 10MB
                                if not content.strip():
                                    continue
                                
                                data = json.loads(content)
                                titles = self.extract_titles(data)
                                if titles:
                                    all_titles.extend(titles)
                                    print(f"✓ Extracted {len(titles)} titles from {filename} using {encoding} encoding")
                                    break
                        except:
                            continue
                    else:
                        print(f"Failed to read {filename} with any encoding")
                        
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                import traceback
                print(f"Full error traceback for {filename}:")
                traceback.print_exc()
                
            # Give user a chance to interrupt
            if idx % 5 == 0:
                print("\nProcessed 5 files. Press Ctrl+C to interrupt (waiting 2 seconds)...")
                try:
                    time.sleep(2)
                except KeyboardInterrupt:
                    print("\nUser interrupted processing. Saving titles found so far...")
                    break
        
        # Remove duplicates and invalid titles
        cleaned_titles = []
        for title in set(all_titles):
            # Remove titles that are too short or contain only special characters
            if len(title) >= 3 and any(c.isalnum() for c in title):
                cleaned_titles.append(title)
            else:
                print(f"Skipping invalid title: {title}")
        
        print(f"\nTotal unique valid titles found: {len(cleaned_titles)}")
        return cleaned_titles

    def extract_songview_data(self, page: Page) -> Dict:
        """Extract data from the BMI Songview results page."""
        data = {
            'title': '',
            'performers': [],
            'writers': [],
            'publishers': [],
            'bmi_work_id': None,
            'iswc': None,
            'shares': {},
            'metadata': {}
        }
        
        try:
            # First check if we're on a no results page
            no_results_selectors = [
                '.no-results',
                '.no-matches',
                ':text("No matching works")',
                ':text("No results found")'
            ]
            
            for selector in no_results_selectors:
                if page.query_selector(selector):
                    print("No results found")
                    return data
            
            # Try to find the results container
            results_selectors = [
                'table.results-table',
                '.songview-results',
                '.work-details',
                '[data-testid="work-details"]'
            ]
            
            results_container = None
            for selector in results_selectors:
                results_container = page.query_selector(selector)
                if results_container:
                    print(f"Found results container with selector: {selector}")
                    break
            
            if not results_container:
                print("Could not find results container")
                return data
            
            # Extract title
            title_selectors = [
                '.work-title',
                '[data-field="title"]',
                'h1.title',
                '.song-title'
            ]
            
            for selector in title_selectors:
                title_elem = results_container.query_selector(selector)
                if title_elem:
                    data['title'] = title_elem.inner_text().strip()
                    print(f"Found title: {data['title']}")
                    break
            
            # Extract BMI Work ID
            id_selectors = [
                '[data-field="bmi_work_id"]',
                '.work-id',
                ':text("BMI Work #")'
            ]
            
            for selector in id_selectors:
                id_elem = results_container.query_selector(selector)
                if id_elem:
                    work_id = id_elem.inner_text().strip()
                    # Clean up the ID if needed
                    work_id = work_id.replace('BMI Work #', '').strip()
                    if work_id:
                        data['bmi_work_id'] = work_id
                        print(f"Found BMI Work ID: {work_id}")
                        break
            
            # Extract ISWC
            iswc_selectors = [
                '[data-field="iswc"]',
                '.iswc',
                ':text("ISWC:")'
            ]
            
            for selector in iswc_selectors:
                iswc_elem = results_container.query_selector(selector)
                if iswc_elem:
                    iswc = iswc_elem.inner_text().strip()
                    # Clean up the ISWC if needed
                    iswc = iswc.replace('ISWC:', '').strip()
                    if iswc:
                        data['iswc'] = iswc
                        print(f"Found ISWC: {iswc}")
                        break
            
            # Extract writers
            writer_rows = results_container.query_selector_all('tr.writer-row, .writer-info')
            for row in writer_rows:
                writer = {
                    'name': '',
                    'role': None,
                    'pro': None,
                    'share': None
                }
                
                # Try different selectors for writer info
                name_elem = row.query_selector('.writer-name, [data-field="writer"]')
                if name_elem:
                    writer['name'] = name_elem.inner_text().strip()
                
                role_elem = row.query_selector('.writer-role, [data-field="role"]')
                if role_elem:
                    writer['role'] = role_elem.inner_text().strip()
                
                pro_elem = row.query_selector('.writer-pro, [data-field="pro"]')
                if pro_elem:
                    writer['pro'] = pro_elem.inner_text().strip()
                
                share_elem = row.query_selector('.writer-share, [data-field="share"]')
                if share_elem:
                    share = share_elem.inner_text().strip().rstrip('%')
                    try:
                        writer['share'] = float(share)
                    except ValueError:
                        pass
                
                if writer['name']:  # Only add if we found a name
                    data['writers'].append(writer)
            
            if data['writers']:
                print(f"Found {len(data['writers'])} writers")
            
            # Extract publishers
            pub_rows = results_container.query_selector_all('tr.publisher-row, .publisher-info')
            for row in pub_rows:
                publisher = {
                    'name': '',
                    'pro': None,
                    'share': None
                }
                
                # Try different selectors for publisher info
                name_elem = row.query_selector('.publisher-name, [data-field="publisher"]')
                if name_elem:
                    publisher['name'] = name_elem.inner_text().strip()
                
                pro_elem = row.query_selector('.publisher-pro, [data-field="pro"]')
                if pro_elem:
                    publisher['pro'] = pro_elem.inner_text().strip()
                
                share_elem = row.query_selector('.publisher-share, [data-field="share"]')
                if share_elem:
                    share = share_elem.inner_text().strip().rstrip('%')
                    try:
                        publisher['share'] = float(share)
                    except ValueError:
                        pass
                
                if publisher['name']:  # Only add if we found a name
                    data['publishers'].append(publisher)
            
            if data['publishers']:
                print(f"Found {len(data['publishers'])} publishers")
            
            # Extract performers
            perf_selectors = [
                '.performer-name',
                '[data-field="performer"]',
                '.artist-name'
            ]
            
            for selector in perf_selectors:
                performers = results_container.query_selector_all(selector)
                if performers:
                    data['performers'] = [p.inner_text().strip() for p in performers if p.inner_text().strip()]
                    print(f"Found {len(data['performers'])} performers")
                    break
            
            # Extract PRO shares
            share_rows = results_container.query_selector_all('tr.share-row, .pro-share')
            for row in share_rows:
                pro_elem = row.query_selector('.pro-name, [data-field="pro"]')
                share_elem = row.query_selector('.share-value, [data-field="share"]')
                
                if pro_elem and share_elem:
                    pro = pro_elem.inner_text().strip()
                    share = share_elem.inner_text().strip().rstrip('%')
                    try:
                        data['shares'][pro] = float(share)
                    except ValueError:
                        pass
            
            if data['shares']:
                print(f"Found shares for {len(data['shares'])} PROs")
            
            # Take a screenshot of successful results for verification
            if data['title']:
                try:
                    page.screenshot(path=os.path.join(self.output_dir, f"success_{data['bmi_work_id'] or datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
                except:
                    pass
            
        except Exception as e:
            print(f"Error extracting data: {str(e)}")
            # Take error screenshot
            try:
                page.screenshot(path=os.path.join(self.output_dir, f"error_extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
            except:
                pass
            
        return data

    def search_bmi(self, title: str, page: Page) -> Dict:
        """Search BMI Songview for a specific title and extract the data."""
        try:
            # Navigate to BMI Songview
            print(f"\nSearching for title: {title}")
            page.goto("https://repertoire.bmi.com/", timeout=30000)
            
            # Wait for the page to be fully loaded
            page.wait_for_load_state("networkidle", timeout=30000)
            print("Page loaded")
            
            # First, wait for and click the search type dropdown
            print("Looking for search type dropdown...")
            dropdown = page.wait_for_selector('select[name="searchType"], select#searchType', timeout=10000)
            if not dropdown:
                print("Could not find search type dropdown")
                return {}
            
            # Click the dropdown and wait a moment
            dropdown.click()
            time.sleep(1)
            print("Clicked search type dropdown")
            
            # Select 'Title' option
            dropdown.select_option('Title')
            time.sleep(1)
            print("Selected 'Title' option")
            
            # Now find and interact with the search input
            print("Looking for search input...")
            search_input = page.wait_for_selector('input[placeholder*="Search"], input[type="text"]', timeout=10000)
            if not search_input:
                print("Could not find search input")
                return {}
            
            # Clear any existing text
            search_input.click()
            search_input.press('Control+A')
            search_input.press('Backspace')
            time.sleep(0.5)
            print("Cleared search input")
            
            # Type the title with a slight delay
            search_input.type(title, delay=50)
            time.sleep(0.5)
            print(f"Typed search term: {title}")
            
            # Look for and click the search button
            print("Looking for search button...")
            search_button = page.wait_for_selector('button[type="submit"], button.search-button', timeout=10000)
            if search_button:
                search_button.click()
                print("Clicked search button")
            else:
                # If no button found, try pressing Enter
                search_input.press('Enter')
                print("Pressed Enter to search")
            
            # Wait for results to load
            print("Waiting for results...")
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # Check for results or no results message
            results_selector = 'table.results-table, .songview-results, .no-results'
            try:
                page.wait_for_selector(results_selector, timeout=15000)
                print("Results section found")
            except:
                print("No results section found")
                return {}
            
            # Take a screenshot for debugging
            try:
                screenshot_path = os.path.join(self.output_dir, f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                page.screenshot(path=screenshot_path)
                print(f"Saved screenshot to {screenshot_path}")
            except:
                pass
            
            # Extract the data
            return self.extract_songview_data(page)
            
        except Exception as e:
            print(f"Error during search: {str(e)}")
            # Take error screenshot
            try:
                page.screenshot(path=os.path.join(self.output_dir, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
            except:
                pass
            return {}

    def run(self):
        """Main method to run the scraper."""
        print("Starting BMI Songview scraper...")
        
        # Read titles from JSON files
        titles = self.read_json_files()
        print(f"Found {len(titles)} unique titles to search")
        
        # Configure proxy settings for Tor
        proxy = {
            "server": "socks5://127.0.0.1:9050"
        }
        
        print("Initializing Playwright...")
        with sync_playwright() as p:
            print("Launching Firefox browser with Tor proxy...")
            try:
                browser = p.firefox.launch(
                    proxy=proxy, # Re-enabled proxy
                    headless=False,  # Make browser visible
                    args=['--no-sandbox']
                )
                print("Browser launched successfully")
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
                )
                print("Browser context created with custom user agent")
                
                page = context.new_page()
                print("New page created")
                
                # Test the connection with retries, increased timeout, and specific waits
                print("Attempting to connect to BMI...")
                max_retries = 2
                connection_successful = False
                for attempt in range(1, max_retries + 1):
                    print(f"Connection attempt {attempt}/{max_retries} (Timeout: 60s)...")
                    try:
                        page.goto("https://repertoire.bmi.com/", timeout=60000) # Increased timeout
                        print("Navigation initiated. Waiting for network idle...")
                        page.wait_for_load_state("networkidle", timeout=60000)
                        print("Network idle. Waiting for search dropdown...")
                        page.wait_for_selector('select#searchType', timeout=60000) # Wait for a specific element
                        print("Successfully loaded BMI website and found search dropdown")
                        connection_successful = True
                        break # Exit loop on success
                    except Exception as e:
                        print(f"Attempt {attempt} failed: {str(e)}")
                        if attempt < max_retries:
                            print("Waiting 5 seconds before retrying...")
                            time.sleep(5)
                        else:
                            print("Max retries reached. Failed to connect to BMI.")
                            raise e # Re-raise the last exception
                            
                if not connection_successful:
                     print("Could not establish connection to BMI after retries.")
                     browser.close()
                     return # Exit if connection failed

                # Process titles
                for idx, title in enumerate(titles, 1):
                    print(f"\nProcessing title {idx}/{len(titles)}: {title}")
                    try:
                        self.search_and_save_work(page, title)
                        # Random delay between requests
                        delay = random.uniform(2, 5)
                        print(f"Waiting {delay:.1f} seconds before next request...")
                        time.sleep(delay)
                    except Exception as e:
                        print(f"Error processing title '{title}': {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"Error launching browser: {str(e)}")
                import traceback
                traceback.print_exc()
                return
                
            finally:
                print("\nClosing browser...")
                browser.close()
            
        print("Scraping completed!")

    def save_results(self, results: Dict, suffix: str):
        """Save results to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"bmi_results_{suffix}_{timestamp}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'total_results': len(results),
                'results': results
            }, f, indent=2, ensure_ascii=False)
            
        print(f"Results saved to {filename}")

    def search_and_save_work(self, page: Page, title: str):
        """Search for a work and save its data."""
        try:
            # Search BMI for the title
            print(f"\nSearching and saving data for: {title}")
            data = self.search_bmi(title, page)
            
            if not data:
                print(f"No data found for title: {title}")
                return
            
            # Add metadata
            data['metadata'] = {
                'search_timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'search_title': title
            }
            
            # Save individual result
            self.save_results({'title': title, 'data': data}, f"work_{title[:30]}")
            print(f"Saved data for: {title}")
            
        except Exception as e:
            print(f"Error in search_and_save_work for '{title}': {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    print("Starting BMI scraper...")
    scraper = BMIScraper()
    scraper.run() # Call the run method which handles browser launch and processing

if __name__ == "__main__":
    main() 