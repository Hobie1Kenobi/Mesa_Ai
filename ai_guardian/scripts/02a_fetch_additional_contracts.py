import os
import requests
from bs4 import BeautifulSoup
import logging
import time
from urllib.parse import urljoin
import tempfile # To save downloaded PDFs temporarily
from pypdf import PdfReader # Ensure pypdf is imported

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

OUTPUT_BASE_DIR = "../data/processed_text" # Save directly to processed text

def save_text(text_content, output_dir, filename):
    """Saves extracted text content to a file."""
    if not text_content:
        logging.warning(f"No text content found to save for {filename}")
        return False
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        cleaned_text = '\n'.join(line.strip() for line in text_content.splitlines() if line.strip())
        if not cleaned_text:
             logging.warning(f"  Extracted text was empty after cleaning for {filename}")
             return False
             
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        logging.info(f"Successfully saved scraped text to {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving text to {filename}: {e}")
        return False

def extract_text_from_pdf(file_path):
    """Extracts text from a .pdf file."""
    # This is duplicated from 03a script - consider moving to a shared utils file later
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if not text and len(reader.pages) > 0:
             logging.warning(f"pypdf extracted no text from PDF {os.path.basename(file_path)}, might be image-based.")
             return None
        return text
    except Exception as e:
        logging.error(f"pypdf Error processing PDF {os.path.basename(file_path)}: {e}")
        return None

def download_file(url, output_path):
    """Downloads a file (like a PDF) from a URL and saves it."""
    # Duplicated/adapted from 02 script
    try:
        response = requests.get(url, stream=True, timeout=30, headers=HEADERS)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"  Downloaded temporary file: {os.path.basename(output_path)}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"  Error downloading {url}: {e}")
        return False
    except Exception as e:
        logging.error(f"  Error saving temporary file {output_path}: {e}")
        return False

def scrape_soundscape(base_url):
    """Scrapes contracts from Soundscape by downloading PDFs and extracting text."""
    output_dir = os.path.join(OUTPUT_BASE_DIR, "Soundscape")
    logging.info(f"--- Scraping Soundscape: {base_url} ---")
    success_count = 0
    try:
        response = requests.get(base_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        agreement_links = []
        for link in soup.find_all('a', href=True):
             href = link['href']
             # Look specifically for the PDF links found previously
             if href.lower().endswith('exclusivesample.pdf') or href.lower().endswith('nonexclusivesample.pdf'):
                 abs_url = urljoin(base_url, href)
                 if abs_url not in [l[0] for l in agreement_links]: 
                      fname_text = os.path.basename(href).replace('.pdf','', 1)
                      txt_filename = f"{fname_text}.txt" 
                      agreement_links.append((abs_url, txt_filename))
                      
        if not agreement_links:
             logging.warning("Could not find PDF agreement links on Soundscape page.")
             return success_count
             
        logging.info(f"Found {len(agreement_links)} PDF agreement links on Soundscape.")
        
        # Create a temporary directory for downloads
        with tempfile.TemporaryDirectory() as tmpdir:
            for url, txt_filename in agreement_links:
                logging.info(f"Processing agreement: {url}")
                time.sleep(1) 
                pdf_filename = os.path.basename(url)
                temp_pdf_path = os.path.join(tmpdir, pdf_filename)
                
                # 1. Download the PDF
                if download_file(url, temp_pdf_path):
                    # 2. Extract text from the downloaded PDF
                    extracted_text = extract_text_from_pdf(temp_pdf_path)
                    # 3. Save the extracted text
                    if save_text(extracted_text, output_dir, txt_filename):
                         success_count += 1
                else:
                    logging.error(f"Skipping text extraction for {url} due to download failure.")
                
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching base Soundscape page {base_url}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during Soundscape scraping: {e}")
        
    return success_count

def scrape_pandadoc(url):
    """Scrapes contract template text from PandaDoc page."""
    output_dir = os.path.join(OUTPUT_BASE_DIR, "PandaDoc")
    logging.info(f"--- Scraping PandaDoc: {url} ---")
    success_count = 0
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        template_div = soup.find('div', class_=lambda x: x and 'template-preview' in x) 
        if not template_div:
            template_div = soup.find('article') 
        if not template_div:
             template_div = soup.find('main') 
             
        if template_div:
            text = template_div.get_text(separator='\n', strip=True)
            filename = "Music_Producer_Contract_Template.txt"
            if save_text(text, output_dir, filename):
                success_count += 1
        else:
            logging.warning("Could not find the template content container on PandaDoc page. Scraping might need updated selectors.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching PandaDoc page {url}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during PandaDoc scraping: {e}")
        
    return success_count

def main():
    logging.info("--- Starting Additional Contract Scraping ---")
    total_saved = 0
    
    total_saved += scrape_soundscape("https://soundscape.io/sample-artist-agreement")
    time.sleep(1)
    
    total_saved += scrape_pandadoc("https://www.pandadoc.com/music-producer-contract-template/")
    
    logging.info(f"--- Scraping Finished. Total new files saved: {total_saved} ---")

import re # Keep if used in scrape_pandadoc selector
if __name__ == "__main__":
    main() 