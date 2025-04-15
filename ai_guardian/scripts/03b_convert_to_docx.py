import os
import logging
import pypandoc
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def convert_to_docx(input_dir, output_dir):
    """Converts .doc, .rtf, and .pdf files in input_dir to .docx in output_dir using pandoc."""
    if not os.path.exists(input_dir):
        logging.error(f"Input directory not found: {input_dir}")
        return

    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Starting conversion to .docx from {input_dir} to {output_dir}")

    # Ensure pandoc is available once at the start
    try:
        pypandoc.ensure_pandoc_installed()
        logging.info("Pandoc installation confirmed.")
    except OSError:
        logging.error("Pandoc not found or accessible. Please install from https://pandoc.org/installing.html and ensure it's in your PATH.")
        return

    converted_count = 0
    copied_count = 0
    error_count = 0
    skipped_count = 0

    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)
        if not os.path.isfile(input_path):
            continue

        base_name, ext = os.path.splitext(filename)
        ext = ext.lower()
        output_filename = f"{base_name}.docx"
        output_path = os.path.join(output_dir, output_filename)

        if ext == '.docx':
            # Just copy existing docx files
            try:
                shutil.copy2(input_path, output_path)
                logging.info(f"Copied existing DOCX: {filename}")
                copied_count += 1
            except Exception as e:
                logging.error(f"Error copying {filename}: {e}")
                error_count += 1
            continue

        # Files to convert
        input_format = None
        if ext == '.doc':
             # Pandoc often uses 'docx' reader for .doc, but we specify 'doc' if possible
             # Let's try letting pandoc infer first, then maybe specify format='doc' if it fails?
             # For now, let pandoc infer based on extension.
             input_format = 'doc' # Explicitly trying doc format again based on pandoc docs
        elif ext == '.rtf':
            input_format = 'rtf'
        elif ext == '.pdf':
             input_format = 'pdf' # Pandoc's PDF support might require extra tools (like pdflatex) sometimes
        else:
            logging.warning(f"Skipping unsupported file type for conversion: {filename}")
            skipped_count += 1
            continue

        logging.info(f"Attempting conversion for: {filename} (Format: {input_format or 'inferred'})")
        try:
            # Convert file to docx
            # Explicitly setting format might help if inference fails.
            pypandoc.convert_file(input_path, 'docx', format=input_format, outputfile=output_path)
            logging.info(f"  Successfully converted to {output_filename}")
            converted_count += 1
        except Exception as e:
            logging.error(f"  Failed to convert {filename}: {e}")
            error_count += 1

    logging.info(f"Conversion complete. Converted: {converted_count}, Copied: {copied_count}, Skipped: {skipped_count}, Errors: {error_count}")

def main():
    raw_contracts_dir = "../data/raw_contracts/HDQTRZ"
    converted_docx_dir = "../data/converted_docx/HDQTRZ"
    
    # Clean out previous results
    if os.path.exists(converted_docx_dir):
         logging.info(f"Cleaning previous results in {converted_docx_dir}")
         shutil.rmtree(converted_docx_dir) # Remove dir and recreate

    convert_to_docx(raw_contracts_dir, converted_docx_dir)

if __name__ == "__main__":
    main() 