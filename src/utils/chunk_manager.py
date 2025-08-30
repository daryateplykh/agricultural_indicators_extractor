import os
import re
from typing import List, Tuple
from langchain_core.documents import Document
from config import Configuration
import collections

class ChunkManager:

    def __init__(self, output_dir: str = Configuration.OUTPUT_PATH):
        self.output_dir = output_dir

    def group_chunks(self, documents: List[Document]) -> dict[Tuple[str, str], List[str]]:
        grouped: dict[Tuple[str, str], List[str]] = {}
        for doc in documents:
            country = doc.metadata.get('country')
            year = doc.metadata.get('year')
            content = doc.page_content
            key = (country, year)
            grouped.setdefault(key, []).append(content)
        return grouped

    def group_and_save(self, documents: List[Document]) -> List[str]:
        grouped = self.group_chunks(documents)
        os.makedirs(self.output_dir, exist_ok=True)
        saved_files: List[str] = []
        for (country, year), chunks in grouped.items():
           
            safe_country = re.sub(r"[^\w\s-]", "", country).replace(" ", "_")
            filename = safe_country
            if year and year != "Unknown":
                filename += f"_{year}"
            filename += ".txt"
            path = os.path.join(self.output_dir, filename)

           
            header = f"Country: {country}\n"
            header += f"Year: {year}\n\n" if year and year != "Unknown" else "\n"
            body = "\n\n".join(chunks)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(header + body)
            saved_files.append(path)
        return saved_files

def aggregate_country_chunks(documents: list[Document]) -> list[Document]:

    country_dir = Configuration.COUNTRY_CHUNKS_PATH
    os.makedirs(country_dir, exist_ok=True)

    country_docs = collections.defaultdict(list)
    for doc in documents:
        key = (
            doc.metadata.get("country", "Unknown"),
            doc.metadata.get("year", "Unknown"),
            doc.metadata.get("source", "Unknown")
        )
        country_docs[key].append(doc)

    aggregated_docs = []
    for key, docs in country_docs.items():
        country, year, source = key
        
        docs.sort(key=lambda d: d.metadata.get("page", 0))
        

        full_content = ""
        for doc in docs:
            page_num = doc.metadata.get("page", 'N/A')
            full_content += doc.page_content + f"\n\n--- END OF PAGE {page_num} ---\n\n"
        

        metadata = {
            "country": country,
            "year": year,
            "source": source,
            "id": f"{source}:{country}:{year}"
        }
        agg_doc = Document(page_content=full_content, metadata=metadata)
        aggregated_docs.append(agg_doc)


        output_filename = os.path.join(country_dir, f"{country}_{year}.txt")
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(full_content)
            
    return aggregated_docs