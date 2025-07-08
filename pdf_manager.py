import os
import pdfplumber
from config import Configuration
from pdf_reader import TextPDFReader
from scanned_pdf_reader import ScannedPDFReader


def process_all_pdfs():
    docs = []
    for fname in os.listdir(Configuration.DATA_PATH):
        path = os.path.join(Configuration.DATA_PATH, fname)
        
        if is_text_pdf(path):
            docs.extend(TextPDFReader().process_single_pdf(path, fname))
        else:
            docs.extend(ScannedPDFReader()._process_single_pdf(path, fname))
      
    return docs 

def is_text_pdf(filepath: str) -> bool:
    with pdfplumber.open(filepath) as pdf:
        return any(page.extract_text() for page in pdf.pages[:2])
