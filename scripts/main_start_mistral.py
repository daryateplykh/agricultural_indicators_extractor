import argparse
from config import Configuration
from src.rag_core.chroma_manager import ChromaManager
from src.data_processing.scan_extractor_mistral import process_all_pdfs

def MainStartMistral():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reset', action='store_true')
    args = parser.parse_args()
    Configuration.initialize()
    if args.reset:
        ChromaManager.clear_database()
    docs = process_all_pdfs()
    chroma = ChromaManager()
    chroma.add_documents(docs)

if __name__ == '__main__':
    MainStartMistral()
