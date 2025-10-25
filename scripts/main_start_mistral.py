import argparse
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from config import Configuration
from src.rag_core.chroma_manager import ChromaManager
from src.data_processing.scan_extractor_mistral import process_all_pdfs
from src.utils.chunk_manager import aggregate_country_chunks
import logging

def MainStartMistral():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reset', action='store_true')
    args = parser.parse_args()
    Configuration.initialize()
    if args.reset:
        ChromaManager.clear_database()
        if os.path.exists(Configuration.OUTPUT_PATH):
            for f in os.listdir(Configuration.OUTPUT_PATH):
                os.remove(os.path.join(Configuration.OUTPUT_PATH, f))
        
    docs = process_all_pdfs()

    logging.info("Aggregating country chunks...")
    country_docs = aggregate_country_chunks(docs)

    chroma = ChromaManager()
    chroma.add_documents(country_docs)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    MainStartMistral()
