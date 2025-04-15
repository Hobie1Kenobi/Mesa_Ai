import os
import logging
from docx import Document
# from striprtf.striprtf import rtf_to_text # No longer needed here
from pypdf import PdfReader
import chardet
# Removed pypandoc import

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_from_docx(file_path):
    """Extracts text from a .docx file."""
    try:
        doc = Document(file_path)
        full_text = [para.text for para in doc.paragraphs]
        return '\n'.join(full_text)
    except Exception as e:
        logging.error(f"python-docx Error processing DOCX {os.path.basename(file_path)}: {e}")
        return None

# Removed extract_text_from_rtf

def extract_text_from_pdf(file_path):
    """Extracts text from a .pdf file."""
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

def process_files(source_dirs, output_dir):
    """Processes specific file types from source directories and saves text to output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Starting text extraction to {output_dir}")
    
    processed_count = 0
    error_count = 0
    skipped_other = 0

    # Process .docx files from converted_docx directory
    docx_dir = source_dirs.get('docx')
    if docx_dir and os.path.exists(docx_dir):
        logging.info(f"Processing DOCX files from {docx_dir}")
        for filename in os.listdir(docx_dir):
            if filename.lower().endswith('.docx'):
                input_path = os.path.join(docx_dir, filename)
                output_filename = f"{os.path.splitext(filename)[0]}.txt"
                output_path = os.path.join(output_dir, output_filename)
                logging.info(f"Processing DOCX: {filename}")
                extracted_text = extract_text_from_docx(input_path)
                if extracted_text:
                    try:
                        cleaned_text = '\n'.join(line.strip() for line in extracted_text.splitlines() if line.strip())
                        if cleaned_text:
                            with open(output_path, 'w', encoding='utf-8') as f:
                                f.write(cleaned_text)
                            logging.info(f"  Successfully extracted text to {output_filename}")
                            processed_count += 1
                        else:
                             logging.warning(f"  Extracted text was empty for {filename}")
                             error_count += 1
                    except Exception as e:
                        logging.error(f"  Error writing text file {output_filename}: {e}")
                        error_count += 1
                else:
                     logging.warning(f"  Failed to extract text from {filename}.")
                     error_count += 1
                     
    # Process .pdf files from raw_contracts directory
    pdf_dir = source_dirs.get('pdf')
    if pdf_dir and os.path.exists(pdf_dir):
        logging.info(f"Processing PDF files from {pdf_dir}")
        for filename in os.listdir(pdf_dir):
             if filename.lower().endswith('.pdf'):
                input_path = os.path.join(pdf_dir, filename)
                output_filename = f"{os.path.splitext(filename)[0]}.txt"
                output_path = os.path.join(output_dir, output_filename)
                logging.info(f"Processing PDF: {filename}")
                extracted_text = extract_text_from_pdf(input_path)
                if extracted_text:
                    try:
                        cleaned_text = '\n'.join(line.strip() for line in extracted_text.splitlines() if line.strip())
                        if cleaned_text:
                            with open(output_path, 'w', encoding='utf-8') as f:
                                f.write(cleaned_text)
                            logging.info(f"  Successfully extracted text to {output_filename}")
                            processed_count += 1
                        else:
                             logging.warning(f"  Extracted text was empty for {filename}")
                             error_count += 1
                    except Exception as e:
                        logging.error(f"  Error writing text file {output_filename}: {e}")
                        error_count += 1
                else:
                     logging.warning(f"  Failed to extract text from {filename}.")
                     error_count += 1
             # Can add handling for other file types here if needed
             elif not filename.lower().endswith(('.doc', '.rtf')): # Avoid double logging skips
                  logging.warning(f"Skipping unsupported file type in PDF source dir: {filename}")
                  skipped_other += 1

    logging.info(f"Text extraction complete. Processed: {processed_count}, Errors/Failed Extraction: {error_count}, Skipped others: {skipped_other}")

def main():
    source_dirs = {
        'docx': "../data/converted_docx/HDQTRZ", # Read .docx from here
        'pdf': "../data/raw_contracts/HDQTRZ"   # Read .pdf from original raw dir
    }
    processed_text_dir = "../data/processed_text/HDQTRZ"
    
    # Clean out previous potentially partial results
    if os.path.exists(processed_text_dir):
         logging.info(f"Cleaning previous results in {processed_text_dir}")
         # Use shutil.rmtree if directory might exist
         try:
             for f in os.listdir(processed_text_dir):
                 os.remove(os.path.join(processed_text_dir, f))
         except FileNotFoundError:
             pass # If dir didn't exist, that's fine
    
    process_files(source_dirs, processed_text_dir)

if __name__ == "__main__":
    main() 