import requests
from bs4 import BeautifulSoup
import os

def fetch_and_save(url, output_dir, filename):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract relevant text content - this might need refinement based on site structure
        # For now, let's get the main text content
        main_content = soup.find('main') or soup.find('body')
        if main_content:
            text_content = main_content.get_text(separator='\n', strip=True)
        else:
            text_content = soup.get_text(separator='\n', strip=True)
        
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Source URL: {url}\n\n")
            f.write(text_content)
            
        print(f"Successfully saved content from {url} to {filepath}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
    except Exception as e:
        print(f"Error processing {url}: {e}")

def main():
    output_base_dir = "../data/raw_legal_info"
    
    rights_info_urls = {
        "US_Copyright_Office": "https://www.copyright.gov/music/",
        "ASCAP": "https://www.ascap.com/help",
        "BMI": "https://www.bmi.com/resources",
        "SESAC": "https://www.sesac.com/"
    }
    
    print("--- Fetching Music Rights Information ---")
    for name, url in rights_info_urls.items():
        fetch_and_save(url, os.path.join(output_base_dir, "rights_info"), f"{name}.txt")

if __name__ == "__main__":
    main() 