import os
import re
from pdf2image import convert_from_path
import pytesseract
from langchain_core.documents import Document
from config import Configuration
from src.utils.country_year_extractor import CountryYearExtractor
from mistralai import Mistral
from PIL import Image as PILImage
from io import BytesIO
import base64
import pdfplumber
from src.utils.image_utils import preprocess_image, split_image_in_half, smart_split_page, is_image_blank
from src.utils.text_utils import clean_ocr_text, stitch_numbers

class ScannedExtractorMistral:
    def __init__(self):
        self.mistral_client = Mistral(api_key=Configuration.API_KEY)

    def extract_text_mistral(self, image: PILImage.Image, year: str, page_num: int = 0, filename: str = "") -> str:
        header_text = pytesseract.image_to_string(
            image.crop((0, 0, image.width, int(image.height * 0.12))), lang='eng', config='--psm 6')
        
        full_text = self._get_ocr_text(image)
        
        return f"{header_text}\n\n{full_text}"

    def _get_ocr_text(self, image: PILImage.Image) -> str:
        if is_image_blank(image):
            return ""

        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        ocr_response = self.mistral_client.ocr.process(
            model=Configuration.OCR_MODEL,
            document={"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}
        )
        

        cleaned_text = clean_ocr_text(ocr_response.pages[0].markdown)
        stitched_text = stitch_numbers(cleaned_text)
        return stitched_text

    @staticmethod
    def is_text_pdf(filepath: str) -> bool:
        try:
            with pdfplumber.open(filepath) as pdf:
                return any(page.extract_text() for page in pdf.pages[:2])
        except:
            return False

    @staticmethod
    def extract_tables_from_page(page) -> list:
        tables = page.extract_tables() or []
        table_chunks = []
        for j, table in enumerate(tables):
            clean_table = [[str(cell or "").strip() for cell in row] for row in table if any(row)]
            table_text = "\n".join([", ".join(row) for row in clean_table])
            table_chunks.append(f"[Table {j}]\n{table_text}")
        return table_chunks

    def _process_single_pdf(self, filepath: str, filename: str) -> list[Document]:
        documents = [] 
        images = convert_from_path(filepath, dpi=300)
        current_country = None
        current_year = "Unknown"
        num_pages = len(images)
        for year in Configuration.YEARS:
            if str(year) in filename:
                current_year = str(year)
                break
        for i, image in enumerate(images):
            preprocessed = preprocess_image(image, current_year)
            
            mistral_text = self.extract_text_mistral(preprocessed, current_year, i, filename)
            current_country = CountryYearExtractor.extract_country(filename, i, mistral_text)
            page_year = current_year
            if not mistral_text.strip():
                continue
            header = f"Country: {current_country}\nYear: {page_year}\nPage: {i}\n\n"
            full_text = header + mistral_text
            
            safe_name = re.sub(r"[^\w\-_.]", "_", f"{current_country}_{page_year}_page{i}.txt")
            out_path = os.path.join(Configuration.OUTPUT_PATH, safe_name)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            
            metadata = {
                "country": current_country,
                "year": page_year,
                "source": filename,
                "page": i,
                "id": f"{filename}:{current_country}:{page_year}:page{i + 1}"
            }
            documents.append(Document(page_content=full_text, metadata=metadata))
        documents = CountryYearExtractor.interpolate_unknown_countries(documents)
        return documents

def process_all_pdfs():
    docs = []
    for fname in os.listdir(Configuration.DATA_PATH):
        if not fname.lower().endswith('.pdf'):
            continue
        path = os.path.join(Configuration.DATA_PATH, fname)
        docs.extend(ScannedExtractorMistral()._process_single_pdf(path, fname))
    return docs 