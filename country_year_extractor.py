import re
from config import Configuration

class CountryYearExtractor:

    @staticmethod
    def extract_country(text: str) -> str | None:
   
        if not text:
            return None
        text_lower = text.lower()
        for country in Configuration.COUNTRIES:
            if country.lower() in text_lower:
                return country
        return None

    @staticmethod
    def extract_year(text: str) -> str:
        if not text:
            return "Unknown"

        if m := re.search(r"\b(19|20)\d{2}/\d{2}\b", text):
            return m.group(0).replace("/", "-")

        if m := re.search(r"\b(19|20)\d{2}\s*[–-]\s*(?:19|20)?\d{2}\b", text):
            return m.group(0).replace("–", "-")

        if m := re.search(r"\b(19|20)\d{2}\b", text):
            return m.group(0)
        return "Unknown"

    @staticmethod
    def extract_year_from_filename(filename: str) -> int | None:
        if m := re.search(r"\b(19|20)\d{2}\b", filename):
            return int(m.group(0))
        return None