import os
import json
import time
import random
from datetime import datetime
from typing import Dict, List
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

class ASCAPScraper:
    def __init__(self, input_dir: str = "output/rights_analysis", output_dir: str = "output/ascap_data"):
        self.input_dir = input_dir
        self.output_dir = os.path.join(output_dir, datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(self.output_dir, exist_ok=True)
        
    def extract_identifiers(self, json_data: Dict) -> List[str]:
        """Extract titles from the works in the JSON data."""
        identifiers = []
        if isinstance(json_data, dict):
            if 'works' in json_data:
                for work in json_data['works']:
                    if isinstance(work, dict) and 'title' in work:
                        # Clean and normalize the title
                        title = work['title'].strip()
                        if title and len(title) >= 3:  # Only include titles with 3 or more characters
                            identifiers.append(title)
        return list(set(identifiers))  # Remove duplicates

    def read_json_files(self) -> List[str]:
        """Read all JSON files in the input directory and extract identifiers."""
        all_identifiers = []
        for filename in os.listdir(self.input_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.input_dir, filename), 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        identifiers = self.extract_identifiers(data)
                        all_identifiers.extend(identifiers)
                        print(f"Extracted {len(identifiers)} identifiers from {filename}")
                except Exception as e:
                    print(f"Error reading {filename}: {str(e)}")
        return list(set(all_identifiers))

    def extract_ascap_data(self, page: Page) -> Dict:
        """Extract data from the ASCAP search results page."""
        data = {
            'performers': [],
            'publishers': [],
            'works': [],
            'metadata': {}
        }
        
        try:
            # Wait for either results or no results message with longer timeout
            results_selector = 'div.results-container, div.no-results-message, table.search-results, div.search-results'
            try:
                page.wait_for_selector(results_selector, timeout=15000)
            except PlaywrightTimeoutError:
                print("No results container found after timeout")
                return data
            
            # Check if we have no results
            no_results = page.query_selector('div.no-results-message, div.no-matches-found, :text("No results found")')
            if no_results:
                print("No results found")
                return data
            
            # Try multiple possible selectors for data
            selectors = {
                'performers': [
                    'td.performer-name', 
                    '.performer-name', 
                    'td[data-type="performer"]',
                    '.result-item .performer',
                    '[data-field="performer"]'
                ],
                'publishers': [
                    'td.publisher-name', 
                    '.publisher-name', 
                    'td[data-type="publisher"]',
                    '.result-item .publisher',
                    '[data-field="publisher"]'
                ],
                'works': [
                    'td.work-title', 
                    '.work-title', 
                    'td[data-type="work"]',
                    '.result-item .title',
                    '[data-field="title"]'
                ]
            }
            
            # Extract performers
            for selector in selectors['performers']:
                performers = page.query_selector_all(selector)
                if performers:
                    data['performers'] = [p.inner_text().strip() for p in performers if p.inner_text().strip()]
                    print(f"Found {len(data['performers'])} performers using selector: {selector}")
                    break
            
            # Extract publishers
            for selector in selectors['publishers']:
                publishers = page.query_selector_all(selector)
                if publishers:
                    for pub in publishers:
                        name = pub.inner_text().strip()
                        if name:
                            pub_data = {
                                'name': name,
                                'id': pub.get_attribute('data-id') if pub.get_attribute('data-id') else None,
                                'ipi': pub.get_attribute('data-ipi') if pub.get_attribute('data-ipi') else None
                            }
                            data['publishers'].append(pub_data)
                    print(f"Found {len(data['publishers'])} publishers using selector: {selector}")
                    break
            
            # Extract works/titles
            for selector in selectors['works']:
                works = page.query_selector_all(selector)
                if works:
                    for work in works:
                        title = work.inner_text().strip()
                        if title:
                            work_data = {
                                'title': title,
                                'id': work.get_attribute('data-id') if work.get_attribute('data-id') else None,
                                'iswc': work.get_attribute('data-iswc') if work.get_attribute('data-iswc') else None
                            }
                            # Try to find associated metadata in parent elements
                            parent = work.evaluate('node => node.closest(".result-item, tr")')
                            if parent:
                                for key in ['year', 'genre', 'duration']:
                                    value_elem = parent.query_selector(f'.{key}, [data-field="{key}"]')
                                    if value_elem:
                                        work_data[key] = value_elem.inner_text().strip()
                            data['works'].append(work_data)
                    print(f"Found {len(data['works'])} works using selector: {selector}")
                    break
            
            # Try to extract any additional metadata
            metadata_selectors = [
                'div.metadata-item',
                '.metadata-row',
                'tr.metadata',
                '.result-item .metadata',
                '[data-type="metadata"]'
            ]
            
            for selector in metadata_selectors:
                metadata_items = page.query_selector_all(selector)
                if metadata_items:
                    for item in metadata_items:
                        key_elem = item.query_selector('.metadata-key, .key, th, [data-field="key"]')
                        value_elem = item.query_selector('.metadata-value, .value, td, [data-field="value"]')
                        if key_elem and value_elem:
                            key = key_elem.inner_text().strip()
                            value = value_elem.inner_text().strip()
                            if key and value:
                                data['metadata'][key] = value
                    if data['metadata']:
                        print(f"Found {len(data['metadata'])} metadata items using selector: {selector}")
                    break
                    
        except PlaywrightTimeoutError as e:
            print(f"Timeout waiting for results: {str(e)}")
        except Exception as e:
            print(f"Error extracting data: {str(e)}")
            
        return data

    def search_ascap(self, identifier: str, page: Page) -> Dict:
        """Search ASCAP for a specific identifier and extract the data."""
        try:
            # Navigate to the ASCAP search page and ensure it's loaded
            page.goto("https://www.ascap.com/repertory", wait_until="networkidle")
            
            # Wait for and verify the search interface is ready
            search_input = page.wait_for_selector('input#searchInput, input[type="search"]', timeout=15000)
            if not search_input:
                print(f"Could not find search input for {identifier}")
                return {}
                
            # Clear any existing text and fill the search input
            search_input.click()
            search_input.fill("")  # Clear existing text
            search_input.type(identifier, delay=100)  # Type with a delay to mimic human input
            
            # Press Enter to submit the search
            search_input.press('Enter')
            
            # Wait for navigation and results to load
            page.wait_for_load_state("networkidle", timeout=15000)
            
            # Check for pagination and gather all results
            all_data = {
                'performers': [],
                'publishers': [],
                'works': [],
                'metadata': {}
            }
            
            page_num = 1
            while True:
                print(f"Processing page {page_num}...")
                
                # Wait for results to load
                time.sleep(3)
                
                # Extract data from current page
                page_data = self.extract_ascap_data(page)
                
                # Merge data from this page
                all_data['performers'].extend(page_data.get('performers', []))
                all_data['publishers'].extend(page_data.get('publishers', []))
                all_data['works'].extend(page_data.get('works', []))
                all_data['metadata'].update(page_data.get('metadata', {}))
                
                # Check for next page button
                next_button = page.query_selector('button.next-page, a.next-page, [aria-label="Next page"]')
                if not next_button or not next_button.is_visible() or not next_button.is_enabled():
                    break
                    
                # Click next page and wait for load
                print("Clicking next page...")
                next_button.click()
                page.wait_for_load_state("networkidle", timeout=15000)
                page_num += 1
            
            print(f"Processed {page_num} pages of results")
            return all_data
            
        except PlaywrightTimeoutError as e:
            print(f"Timeout error searching for {identifier}: {str(e)}")
            return {}
        except Exception as e:
            print(f"Error searching for {identifier}: {str(e)}")
            return {}

    def run(self):
        """Main method to run the scraper."""
        print("Starting ASCAP scraper...")
        
        # Read identifiers from JSON files
        identifiers = self.read_json_files()
        print(f"Found {len(identifiers)} unique identifiers to search")
        
        # Initialize Playwright with Tor proxy
        with sync_playwright() as p:
            print("Launching browser with Tor proxy...")
            browser = p.chromium.launch(
                proxy={
                    "server": "socks5://127.0.0.1:9050"
                },
                headless=False  # Set to True for production
            )
            
            context = browser.new_context()
            page = context.new_page()
            
            # Verify Tor connection
            print("Verifying Tor connection...")
            try:
                page.goto("https://check.torproject.org", wait_until="networkidle")
                if page.query_selector("body:has-text('Congratulations')"):
                    print("Successfully connected through Tor")
                else:
                    print("Warning: May not be connected through Tor")
            except Exception as e:
                print(f"Error checking Tor connection: {str(e)}")
            
            # Process each identifier
            results = {}
            for idx, identifier in enumerate(identifiers, 1):
                print(f"\nProcessing {idx}/{len(identifiers)}: {identifier}")
                print("Navigating to ASCAP search page...")
                
                try:
                    data = self.search_ascap(identifier, page)
                    if data.get('performers') or data.get('publishers') or data.get('works'):
                        print(f"Found data: {len(data.get('performers', []))} performers, "
                              f"{len(data.get('publishers', []))} publishers, "
                              f"{len(data.get('works', []))} works")
                        results[identifier] = data
                    else:
                        print("No data found")
                    
                    # Save intermediate results
                    if idx % 10 == 0:
                        print(f"Saving batch {idx//10}...")
                        self.save_results(results, f"batch_{idx//10}")
                        
                    # Add delay between requests
                    delay = 2 + random.uniform(1, 3)  # Random delay between 3-5 seconds
                    print(f"Waiting {delay:.1f} seconds before next request...")
                    time.sleep(delay)
                    
                except Exception as e:
                    print(f"Error processing {identifier}: {str(e)}")
                    continue
            
            # Save final results
            print("\nSaving final results...")
            self.save_results(results, "final")
            
            context.close()
            browser.close()
            
        print("Scraping completed!")

    def save_results(self, results: Dict, suffix: str):
        """Save results to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"ascap_results_{suffix}_{timestamp}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'total_results': len(results),
                'results': results
            }, f, indent=2, ensure_ascii=False)
            
        print(f"Results saved to {filename}")

def main():
    scraper = ASCAPScraper()
    scraper.run()

if __name__ == "__main__":
    main() 