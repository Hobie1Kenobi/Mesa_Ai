import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# Define a common User-Agent header
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def download_file(url, output_path):
    """Downloads a file from a URL and saves it."""
    try:
        # Add User-Agent header to the download request
        response = requests.get(url, stream=True, timeout=20, headers=HEADERS)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  Downloaded: {os.path.basename(output_path)}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  Error downloading {url}: {e}")
        return False
    except Exception as e:
        print(f"  Error saving {output_path}: {e}")
        return False

def fetch_hdqtrz_contracts(base_url, output_dir):
    """Fetches contracts from the HDQTRZ free contracts page."""
    print(f"Fetching contracts from {base_url}...")
    try:
        # Add User-Agent header to the initial page request
        response = requests.get(base_url, timeout=15, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all list items, assuming each contract is in an <li>
        # This structure might need adjustment if the site changes
        # We target links within list items as a starting point
        # Focusing on sections implicitly by filenames for now
        relevant_keywords = [
            'songwriter', 'publisher', 'composer', 'copyright', 
            'license', 'publishing', 'split-sheet', 'option'
        ]
        
        download_links = []
        list_items = soup.find_all('li') # Adjust selector if needed based on actual site structure

        if not list_items:
             # Fallback: find all download links if <li> structure isn't found
             print("  Warning: Could not find list items (<li>), attempting to find all download links.")
             links = soup.find_all('a', href=True)
        else:
             links = soup.find_all('a', href=True)


        for link in links:
            href = link['href']
            link_text = link.get_text(strip=True).lower()
            filename = os.path.basename(href).lower()

            # Check if 'download' text is present or filename matches keywords
            is_download_link = 'download' in link_text 
            
            # Check if filename contains relevant keywords and has a doc/rtf extension
            is_relevant_file = any(keyword in filename for keyword in relevant_keywords) and \
                               (filename.endswith('.doc') or filename.endswith('.rtf') or filename.endswith('.pdf'))

            if href and (is_download_link or is_relevant_file):
                # Ensure it's a document file we might be interested in
                 if filename.endswith(('.doc', '.rtf', '.pdf')):
                    absolute_url = urljoin(base_url, href)
                    # Avoid duplicates
                    if absolute_url not in [d[0] for d in download_links]:
                         # Use the link text or fallback to filename if text is just 'Download'
                        contract_name = link.get_text(strip=True)
                        if contract_name.lower() == 'download' or not contract_name:
                             contract_name = os.path.basename(href) # Get filename from URL
                        
                        # Sanitize filename slightly (replace spaces, etc.) - basic example
                        safe_filename = contract_name.replace(' ', '_').replace('/','_')
                        # Ensure it keeps original extension
                        base, ext = os.path.splitext(os.path.basename(href))
                        if not safe_filename.endswith(ext):
                             safe_filename += ext

                        output_path = os.path.join(output_dir, safe_filename)
                        download_links.append((absolute_url, output_path))

        print(f"Found {len(download_links)} potential contract links.")

        downloaded_count = 0
        for url, output_path in download_links:
            if download_file(url, output_path):
                downloaded_count += 1
            time.sleep(0.5) # Add a small delay between downloads

        print(f"Successfully downloaded {downloaded_count} contracts.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {base_url}: {e}")
    except Exception as e:
        print(f"An error occurred during scraping: {e}")


def main():
    output_dir = "../data/raw_contracts"
    os.makedirs(output_dir, exist_ok=True)

    # Updated contract_sources dictionary
    contract_sources = {
        "HDQTRZ": "https://www.hdqtrz.com/free-contracts/",
        # "RocketLawyer": "https://www.rocketlawyer.com/business-and-contracts/intellectual-property/music-contracts" # Keep this commented out or handle separately
    }

    print("--- Fetching Sample Music Contracts ---")
    for name, url in contract_sources.items():
        site_output_dir = os.path.join(output_dir, name)
        os.makedirs(site_output_dir, exist_ok=True)
        if name == "HDQTRZ":
            fetch_hdqtrz_contracts(url, site_output_dir)
        # else: # Placeholder for other sites like RocketLawyer if needed
            # print(f"Skipping {name} ({url}) - Implementation needed.")


if __name__ == "__main__":
    main() 