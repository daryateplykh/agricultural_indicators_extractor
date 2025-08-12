import os
import re
from pdf2image import convert_from_path
import pytesseract
from langchain_core.documents import Document
from config import Configuration
from src.utils.country_year_extractor import CountryYearExtractor
from mistralai import Mistral
from PIL import Image as PILImage, ImageEnhance
from io import BytesIO
import base64
import pdfplumber
from src.utils.image_utils import preprocess_image, split_image_in_half, smart_split_page, split_image_horizontally

class ScannedExtractorMistral:
    def __init__(self):
        self.mistral_client = Mistral(api_key=Configuration.API_KEY)

    def extract_text_mistral(self, image: PILImage.Image, year: str, page_num: int = 0) -> str:
        header_text = pytesseract.image_to_string(
            image.crop((0, 0, image.width, int(image.height * 0.12))), lang='eng', config='--psm 6')
        
        if year == '1930':
            left_half, right_half = split_image_in_half(image)
            mistral_text_left = self._get_ocr_text(left_half)
            mistral_text_right = self._get_ocr_text(right_half)
            combined_text = f"{mistral_text_left}\n\n{mistral_text_right}"
        else:
            left_col, right_col = smart_split_page(image)
            
            top_left, bottom_left = split_image_horizontally(left_col)
            top_right, bottom_right = split_image_horizontally(right_col)

            text_tl = self._get_ocr_text(top_left)
            text_bl = self._get_ocr_text(bottom_left)
            text_tr = self._get_ocr_text(top_right)
            text_br = self._get_ocr_text(bottom_right)

            left_full_text = f"{text_tl}\n\n{text_bl}"
            right_full_text = f"{text_tr}\n\n{text_br}"
            combined_text = f"{left_full_text}\n\n{right_full_text}"

        return f"{header_text}\n\n{combined_text}"

    def _get_ocr_text(self, image: PILImage.Image) -> str:
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        ocr_response = self.mistral_client.ocr.process(
            model="mistral-ocr-latest",
            document={"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}
        )
        return ocr_response.pages[0].markdown

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
            preprocessed = preprocess_image(image)
            mistral_text = self.extract_text_mistral(preprocessed, current_year, i)
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