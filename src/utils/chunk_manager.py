import os
import re
from typing import List, Tuple
from langchain_core.documents import Document
from config import Configuration

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
