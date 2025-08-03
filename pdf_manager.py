import os
from config import Configuration
from scanned_pdf_reader import ScannedPDFReader


def process_all_pdfs():
    docs = []
    for fname in os.listdir(Configuration.DATA_PATH):
        path = os.path.join(Configuration.DATA_PATH, fname)
        docs.extend(ScannedPDFReader()._process_single_pdf(path, fname))
      
    return docs
