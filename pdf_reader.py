import os
import re
import pdfplumber
from langchain_core.documents import Document
from config import Configuration
from country_year_extractor import CountryYearExtractor

class TextPDFReader:
    def __init__(self):
        self.meta = CountryYearExtractor()

    def process_single_pdf(self, filepath: str, filename: str):
        country_chunks: dict[tuple[str, str], list[str]] = {}
        current_country: str | None = None
        current_year: str | None = None

#Открытие PDF и обход страниц
        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if not text:
                    continue

#бновление метаданных по тексту страницы
                c = self.meta.extract_country(text)
                y = self.meta.extract_year(text)
                if c:
                    current_country = c
                if y is not None:
                    current_year = y

                if not current_country or current_year is None:
                    continue

#Извлечение таблиц и формирование чанков
                key = (current_country, current_year)
                for tbl_idx, table in enumerate(page.extract_tables() or []):
                    clean = [
                        [str(cell or "").strip() for cell in row]
                        for row in table if any(row)
                    ]
                    table_text = "\n".join(", ".join(r) for r in clean)
                    chunk = f"[Page {page_num} | Table {tbl_idx}]\n{table_text}"
                    country_chunks.setdefault(key, []).append(chunk)

# тут начинается сохранение чанков
        documents = []
        for (country, year), chunks in country_chunks.items():
            if not country or year is None or not chunks:
                continue
            header = f"Country: {country}\nYear: {year}\n\n"
            full_text = header + "\n\n".join(chunks)
            safe_name = re.sub(r"[^\w\-_.]", "_", f"{country}_{year}.txt")
            out_path = os.path.join(Configuration.OUTPUT_PATH, safe_name)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            print(f" Сохранён чанк {safe_name}")
            metadata = {
                "country": country,
                "year": year,
                "source": filename,
                "id": f"{filename}:{country}:{year}"
            }
            documents.append(Document(page_content=full_text, metadata=metadata))
        return documents
