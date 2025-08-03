import os
import re
from rapidfuzz import fuzz
from config import Configuration
from langchain_core.documents import Document

MANUAL_COUNTRY_MAPPING = {
    ("1950_1SamoeAustralia.pdf", 0): "American Samoa",
    ("1950_1new.pdf", 3): "Australia",
    ("1950_1new.pdf", 4): "Australia",
    ("1950_1new.pdf", 5): "Australia",
    ("1950_1new.pdf", 6): "Australia",
}

class CountryExtractor:
    @staticmethod
    def fuzzy_extract_country(text: str, threshold=80) -> str | None:
        if not text:
            return None
        text_lower = text.lower()
        best_country = None
        best_score = 0
        for country in Configuration.COUNTRIES:
            score = fuzz.partial_ratio(country.lower(), text_lower)
            if score > best_score:
                best_score = score
                best_country = country
        if best_score >= threshold:
            return best_country
        return None

    @staticmethod
    def extract_country(filename: str, page_index: int, text: str) -> str:
        manual_country = MANUAL_COUNTRY_MAPPING.get((filename, page_index))
        if manual_country:
            return manual_country
        
        fuzzy_country = CountryExtractor.fuzzy_extract_country(text, threshold=80)
        if fuzzy_country:
            return fuzzy_country
        
        return "Unknown"

    @staticmethod
    def interpolate_unknown_countries(documents: list[Document]) -> list[Document]:
        n = len(documents)
        countries = [doc.metadata["country"] for doc in documents]
        i = 0
        while i < n:
            if countries[i] == "Unknown":
                start = i
                while i < n and countries[i] == "Unknown":
                    i += 1
                end = i - 1
                country_before = countries[start - 1] if start > 0 else None
                country_after = countries[end + 1] if end + 1 < n else None
                if country_before and country_after and country_before == country_after:
                    for j in range(start, end + 1):
                        old_country = documents[j].metadata["country"]
                        documents[j].metadata["country"] = country_before
                        page_year = documents[j].metadata["year"]
                        page_num = documents[j].metadata["page"]
                        header = f"Country: {country_before}\nYear: {page_year}\nPage: {page_num}\n\n"
                        old_text = documents[j].page_content
                        body = old_text.split("\n\n", 1)[-1] if "\n\n" in old_text else old_text
                        new_full_text = header + body
                        documents[j].page_content = new_full_text
                        filename = documents[j].metadata["source"]
                        safe_name = re.sub(r"[^\w\-_.]", "_", f"{country_before}_{page_year}_page{page_num}.txt")
                        out_path = os.path.join(Configuration.OUTPUT_PATH, safe_name)
                        old_safe_name = re.sub(r"[^\w\-_.]", "_", f"{old_country}_{page_year}_page{page_num}.txt")
                        old_out_path = os.path.join(Configuration.OUTPUT_PATH, old_safe_name)
                        if old_safe_name != safe_name and os.path.exists(old_out_path):
                            os.remove(old_out_path)
                        with open(out_path, "w", encoding="utf-8") as f:
                            f.write(new_full_text)
            else:
                i += 1
        return documents 