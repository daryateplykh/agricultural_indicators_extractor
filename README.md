# agricultural_indicators_extractor
This repository accompanies the paper *"A longitudinal database of agricultural indicators from 1930 to 1960"*.

## Abstract
Agricultural indicators are important for understanding long-term changes in farming systems. However, historical data, such as agricultural reports, are typically contained in non-machine-readable documents and are unavailable in a structured format, which makes their analysis difficult. Here, we present a new dataset covering 130 countries and 275 harmonized agricultural indicators from 1930 to 1960. Our dataset includes 12,090 unique country–year observations and includes key indicators of farm structure and agricultural intensity, such as farm population, number and area of holdings, and crop area and production (e.g., rye and millet). We created the dataset using a large language model (LLM), which we used to extract structured data from archived FAO World Census of Agriculture (WCA) reports. We validated the LLM-based pipeline a manual validation, where the LLM pipeline achieves an accuracy of 80.3\%. We further compared our LLM pipeline against external databases, which are less comprehensive and are often derived from secondary sources rather than the raw country reports. Our dataset fills important gaps in existing historical data, as many values were previously missing or unstructured. Overall, the result represents a new resource for agricultural monitoring, enabling more comprehensive comparisons across countries and supporting policy development in the context of environmental change and long-term sustainable development planning.

## Project Structure

```
Rag_Pipline_Thesis_Teplykh/
├── chroma/                  # ChromaDB vector store
├── config.py                # Configuration file (paths, countries, years)
├── data/                    # Input PDF files
│   └── rag_outputs/         # RAG query results and CSV outputs
├── scripts/                 # Main scripts to run the pipeline
│   ├── main_start_mistral.py  # Main script to process PDFs with Mistral
│   ├── main_start_paddle.py   # Main script to process PDFs with PaddleOCR
│   ├── batch_rag_runner.py    # Script to run batch queries
├── test/                    # Scripts for testing and validating the extraction pipeline
└── src/                     # Source code
    ├── data_processing/       # Scripts for PDF processing and text extraction
    ├── rag_core/              # Core RAG components (ChromaDB, querying)
    └── utils/                 # Utility functions
```


## Installation
### Prerequisites

Before running this project, make sure you have the following:

- **Python 3.8+** (for running the RAG pipeline to extract agricultural indicators)
- **[Mistral AI](https://mistral.ai/) API key** - set as `MISTRAL_API_KEY` in `.env` (for OCR processing of scanned PDF documents)
- **[Together AI](https://www.together.ai/) API key** - set as `TOGETHER_API_KEY` in `.env` (for LLM access during question answering)
- **[Hugging Face](https://huggingface.co/) account** (for embedding model access during similarity search)


### Setup instructions
#### System Dependencies

This project requires **Poppler** for PDF processing. 

```bash
conda install -c conda-forge poppler
``` 

#### Python environment
Install the required Python packages:

```bash
pip3 install -r requirements.txt
```

#### Environment configuration
Create a `.env` file in the project root directory with the following variables:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
TOGETHER_API_KEY=your_together_api_key_here
```

### Download the dataset

To reproduce the results, download the required data from FAO Statistics Division as follows:

1. Download the required data archive from [FAO Statistics Division]( https://www.fao.org/statistics/resources/3/en?indexCatalogue=search-index-statistics&wordsMode=AllWords&fallbacklang=en&tags=299a3613-92eb-4458-92a5-40ad0ff55bff&searchQuery=*%3a*&tabInx=0).

2. Place the contents into the `data/` folder located in the root directory of the repository.

## Data Description

For detailed information about the structure and format of the extracted data, see [DATA_OUTPUTS_DESCRIPTION.md](DATA_OUTPUTS_DESCRIPTION.md).

## Usage

This repository consists of three main components:

1. **PDF processing and OCR** using Mistral AI (Python)
2. **Agricultural indicators-extractor** using retrieval-augmented generation (RAG) (Python)
3. **Data validation and accuracy assessment** of extracted agricultural indicators (Python)

### 1. Processing PDFs

To process the PDF files located in the `data/` directory and extract text into `output_chunks/`, you can use either Mistral or PaddleOCR.

**Using Mistral OCR:**
```bash
python -m scripts.main_start_mistral
```
This script will process the PDFs, extract text using Mistral's OCR, and store the results in a ChromaDB vector store.

### 2. Extract agricultural indicators

After processing the PDFs, you can ask questions about the data using the RAG pipeline.

**Single Query:**
You can query the RAG pipeline directly from the command line:
```bash
python -m src.rag_core.rag_answer "Your question here"
```

The answer will be printed to the console, and a `output.csv` file will be created if a table is found in the response.

**Batch Queries:**
To run multiple queries from a file, you can use the `batch_rag_runner.py` script. The queries are defined in `scripts/queries.yaml`.
```bash
python -m scripts.batch_rag_runner
```

### 3. Data validation and accuracy assessment

The project includes two comprehensive validation systems to assess the accuracy of the LLM-based data extraction pipeline:

**Manual validation:**
This test compares extracted data with the human-annotated dataset.
```bash
cd test
python manual_validation.py
```

**Benchmarking against Existing Databases:**
The extracted dataset was also compared against independent agricultural databases.
```bash
cd test
python benchmarking_validation.py
```
