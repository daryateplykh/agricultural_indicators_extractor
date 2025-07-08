import argparse
from config import Configuration
from pdf_reader import TextPDFReader
from chroma_manager import ChromaManager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reset', action='store_true')
    args = parser.parse_args()

    Configuration.initialize()

    if args.reset:
        ChromaManager.clear_database()

    processor = TextPDFReader()
    docs = processor.process_pdfs()
    
    chroma = ChromaManager()
    chroma.add_documents(docs)

if __name__ == '__main__':
    main()