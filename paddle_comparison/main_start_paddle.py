import argparse
import os
import re
import shutil
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Configuration
from paddle_comparison.scan_extractor_paddle import process_pdf_paddle
from paddleocr import PaddleOCR


def save_documents(documents: list):
    saved_count = 0
    os.makedirs(Configuration.OUTPUT_PATH, exist_ok=True)
    
    for doc in documents:
        country = doc.metadata.get("country", "Unknown")
        year = doc.metadata.get("year", "Unknown")
        page = doc.metadata.get("page", 0)
        
        safe_filename = re.sub(r"[^\w\-_.]", "_", f"{country}_{year}_page{page}.txt")
        out_path = os.path.join(Configuration.OUTPUT_PATH, safe_filename)
        
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(doc.page_content)
            saved_count += 1
        except Exception as e:
            pass
    
    return saved_count

def main():
    parser = argparse.ArgumentParser(description="PDF -> OCR -> TXT (with column splitting)")
    parser.add_argument('--reset', action='store_true')
    args = parser.parse_args()
    
    Configuration.initialize()
    
    if args.reset and os.path.exists(Configuration.OUTPUT_PATH):
        shutil.rmtree(Configuration.OUTPUT_PATH)
    
    os.makedirs(Configuration.OUTPUT_PATH, exist_ok=True)
    
    if not os.path.exists(Configuration.DATA_PATH):
        return
        
    pdf_files = [f for f in os.listdir(Configuration.DATA_PATH) if f.lower().endswith(".pdf")]
    if not pdf_files:
        return

    ocr = PaddleOCR(lang="en", use_textline_orientation=True)
    all_documents = []

    for filename in pdf_files:
        filepath = os.path.join(Configuration.DATA_PATH, filename)
        documents = process_pdf_paddle(filepath, filename, ocr)
        all_documents.extend(documents)
        
    if not all_documents:
        return
        
    save_documents(all_documents)
    

if __name__ == '__main__':
    main()
