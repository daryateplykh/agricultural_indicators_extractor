This project is a RAG (Retrieval-Augmented Generation) pipeline designed to extract structured data from agricultural census reports in PDF format. It uses OCR to process scanned documents, a vector database to store text chunks, and a large language model to answer questions based on the extracted information.

## Project Structure

Rag_Pipline_Thesis_Teplykh/
├── chroma/                  # ChromaDB vector store
├── config.py                # Configuration file (paths, countries, years)
├── data/                    # Input PDF files
├── env/                     # Python virtual environment
├── output_chunks/           # Processed text chunks from PDFs
├── requirements.txt         # Python dependencies
├── scripts/                 # Main scripts to run the pipeline
│   ├── main_start_mistral.py  # Main script to process PDFs with Mistral
│   ├── main_start_paddle.py   # Main script to process PDFs with PaddleOCR
│   ├── batch_rag_runner.py    # Script to run batch queries
│   └── performance_comparator.py # Script to compare OCR performance
└── src/                     # Source code
    ├── data_processing/       # Scripts for PDF processing and text extraction
    ├── rag_core/              # Core RAG components (ChromaDB, querying)
    └── utils/                 # Utility functions



## Setup and Installation
1.  Create and activate a Python virtual environment:
    python -m venv env
    On Windows: .\env\Scripts\activate
     On macOS/Linux:source env/bin/activate

2.  Install the required dependencies:
    
    

## Configuration
1.  Create a `.env` file in the root directory of the project. This file will store your API key for the Mistral API.

2. Add your API key to the `.env` file:
    API_KEY="your_mistral_api_key_here"
    ** for tests you can use my key: API_KEY=Y1zsb7LjEcxjKmzaqcEIxEtjN2C4jOOU 
    


## Usage
1. Processing PDFs

To process the PDF files located in the `data/` directory and extract text into `output_chunks/`, you can use either Mistral or PaddleOCR.

*   Using Mistral OCR: python -m scripts.main_start_mistral

    This script will process the PDFs, extract text using Mistral's OCR, and store the results in a ChromaDB vector store.

*   Using PaddleOCR: python -m scripts.main_start_paddle
    
    This script performs the same function but uses PaddleOCR for text extraction.

2. Querying the Data

After processing the PDFs, you can ask questions about the data using the RAG pipeline.

*   **Single Query:**
    You can query the RAG pipeline directly from the command line:
    python -m src.rag_core.rag_answer "Your question here"

    For example:
    python -m src.rag_core.rag_answer "What was the total area of farms in Cyprus in 1950?"

    The answer will be printed to the console, and a `output.csv` file will be created if a table is found in the response.

*   **Batch Queries:**
    To run multiple queries from a file, you can use the `batch_rag_runner.py` script. The queries are defined in `scripts/queries.yaml`.
    python -m scripts.batch_rag_runner

## Testing

This project includes a test suite to validate the RAG model's accuracy on a predefined set of questions. `scripts/run_tests.py`.

I use this suite only to compare Paddle and Mistral. The main code to validate the results will be created later.

Additionally. Comparing OCR Performance

To compare the performance of Mistral and PaddleOCR, you can run the `performance_comparator.py` script: python -m scripts.performance_comparator
This will generate a `performance_comparison_report.txt` file in the `output_chunks/` directory.