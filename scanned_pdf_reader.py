import os
import re
from pdf2image import convert_from_path
import pytesseract
from langchain_core.documents import Document
from config import Configuration
from country_year_extractor import CountryYearExtractor
from mistralai import Mistral
from PIL import Image as PILImage, ImageEnhance
from io import BytesIO
import base64
import pdfplumber

class ScannedPDFReader:
    def __init__(self):
        self.meta = CountryYearExtractor()
        self.mistral_client = Mistral(api_key=Configuration.API_KEY)

    def preprocess_image(self, image: PILImage.Image) -> PILImage.Image:

        image = image.resize((image.width * 2, image.height * 2), PILImage.LANCZOS)

        image = image.convert('L')

        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        image = image.point(lambda x: 0 if x < 180 else 255, '1')
        return image

    def extract_text_mistral(self, image: PILImage.Image) -> str:
        header_text = pytesseract.image_to_string(
            image.crop((0, 0, image.width, int(image.height * 0.12))), lang='eng', config='--psm 6')
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        base64image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        ocr_response = self.mistral_client.ocr.process(
            model="mistral-ocr-latest",
            document={"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64image}"}
        )
        mistral_text = ocr_response.pages[0].markdown
        return f"{header_text}\n\n{mistral_text}"

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

    def _get_found_keywords(self, text: str) -> list:
        if not text:
            return []
        text_lower = text.lower()
        return [kw for kw in Configuration.KEYWORDS if kw.lower() in text_lower]

    def _process_single_pdf(self, filepath: str, filename: str) -> list[Document]:
        print(f"\nОбработка сканированного PDF: {filename}")
        documents = []
        images = convert_from_path(filepath, dpi=300)
        current_country = None
        current_year = "Unknown"
        for i, image in enumerate(images):
            print(f"\n Страница {i+1}/{len(images)}")
            preprocessed = self.preprocess_image(image)
            tesseract_text = pytesseract.image_to_string(preprocessed, lang='eng', config='--psm 6')
            print(f" Результат pytesseract: {repr(tesseract_text[:100])}...")
            c = self.meta.extract_country(tesseract_text)
            y = self.meta.extract_year(tesseract_text)
            if c:
                current_country = c
                print(f"Найдена страна: {current_country}")
            if y != "Unknown":
                current_year = y
                print(f"Найден год: {current_year}")
            if not current_country:
                print("Страна не найдена — пропуск страницы")
                continue
            found_keywords = self._get_found_keywords(tesseract_text)
            if found_keywords:
                print(f"  Найдены ключевые слова: {found_keywords} — отправляем страницу в Mistral OCR")
                mistral_text = self.extract_text_mistral(image)
                print(f"Результат Mistral OCR: {repr(mistral_text[:100])}...")
                
                #### print(" ????? Пустой текст от Mistral — пропуск")
                if not mistral_text.strip():
                    print(" ????? Пустой текст от Mistral — пропуск")
                    continue
                header = f"Country: {current_country}\nYear: {current_year}\nPage: {i}\n\n"
                full_text = header + mistral_text
                safe_name = re.sub(r"[^\w\-_.]", "_", f"{current_country}_{current_year}_page{i}.txt")
                out_path = os.path.join(Configuration.OUTPUT_PATH, safe_name)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(full_text)
                print(f"Сохранён чанк: {safe_name}")
                metadata = {
                    "country": current_country,
                    "year": current_year,
                    "source": filename,
                    "page": i,
                    "id": f"{filename}:{current_country}:{current_year}:page{i}"
                }
                documents.append(Document(page_content=full_text, metadata=metadata))
        return documents 