import os
import re
import argparse
import shutil
from typing import List
import numpy as np
import cv2
from pdf2image import convert_from_path
from paddleocr import PaddleOCR
from langchain_core.documents import Document

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Configuration
from country_year_extractor import CountryYearExtractor
from image_utils import preprocess_image


def extract_text_paddle(ocr: PaddleOCR, pil_img, header_ratio: float = 0.12) -> str:
    H = int(pil_img.height * header_ratio)
    header_crop = pil_img.crop((0, 0, pil_img.width, H))
    header_np = np.array(header_crop)
    header_text = _ocr_np(ocr, header_np).strip()

    from image_utils import smart_split_page
    left_img, right_img = smart_split_page(pil_img)

    left_np = np.array(left_img)
    right_np = np.array(right_img)

    left_text = _ocr_np(ocr, left_np).strip()
    right_text = _ocr_np(ocr, right_np).strip()

    parts = [t for t in [header_text, left_text, right_text] if t]
    return "\n\n".join(parts).strip()

def _ocr_np(ocr: PaddleOCR, img_np: np.ndarray) -> str:
    processed = preprocess_for_ocr(img_np)
    try:
        pred = ocr.predict(processed)
        txts = collect_texts(pred)
        joined = "\n".join(txts).strip()
        if joined:
            return joined
    except Exception:
        pass
    try:
        res = ocr.ocr(processed, use_textline_orientation=True)
        txts = collect_texts(res)
        return "\n".join(txts).strip()
    except Exception:
        return ""

def preprocess_for_ocr(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        gray = img
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.medianBlur(gray, 3)
    gray = cv2.equalizeHist(gray)
    rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    return rgb

def collect_texts(result_obj) -> List[str]:
    texts: List[str] = []
    def has_alnum(s: str) -> bool:
        return any(ch.isalnum() for ch in s)
    def walk(x):
        if x is None:
            return
        if isinstance(x, dict):
            v = x.get("text") or x.get("transcription")
            if isinstance(v, str) and v.strip():
                texts.append(v.strip())
            for vv in x.values():
                if isinstance(vv, (list, tuple, dict, str)):
                    walk(vv)
            return
        if isinstance(x, str):
            if has_alnum(x):
                texts.append(x.strip())
            return
        if isinstance(x, (list, tuple)):
            if len(x) >= 2:
                snd = x[1]
                if isinstance(snd, (list, tuple)) and snd and isinstance(snd[0], str):
                    if has_alnum(snd[0]):
                        texts.append(snd[0].strip())
            for item in x:
                if isinstance(item, (list, tuple, dict, str)):
                    walk(item)
    walk(result_obj)
    seen = set()
    uniq = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq

def main():
    parser = argparse.ArgumentParser(description="PDF -> OCR -> TXT (деление на 2 колонки)")
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    Configuration.initialize()

    if args.reset and os.path.exists(Configuration.OUTPUT_PATH):
        shutil.rmtree(Configuration.OUTPUT_PATH)

    os.makedirs(Configuration.OUTPUT_PATH, exist_ok=True)

    if not os.path.exists(Configuration.DATA_PATH):
        return

    pdf_files = [f for f in os.listdir(Configuration.DATA_PATH) if f.lower().endswith(".pdf")]
    ocr = PaddleOCR(lang="en", use_textline_orientation=True)

    for filename in pdf_files:
        filepath = os.path.join(Configuration.DATA_PATH, filename)
        
        current_year = "Unknown"
        for year in Configuration.YEARS:
            if str(year) in filename:
                current_year = str(year)
                break
        
        try:
            images = convert_from_path(filepath, dpi=args.dpi)
        except Exception as e:
            print(f"Ошибка при конвертации PDF {filename}: {e}")
            continue

        for page_idx, pil_img in enumerate(images):
            combo_text = extract_text_paddle(ocr, pil_img)

            if not combo_text.strip():
                continue
            
            current_country = CountryYearExtractor.extract_country(filename, page_idx, combo_text)
            
            header = f"Country: {current_country}\nYear: {current_year}\nPage: {page_idx}\n\n"
            full_text = header + combo_text
            

            safe_filename = re.sub(r"[^\w\-_.]", "_", f"{current_country}_{current_year}_page{page_idx}.txt")
            out_path = os.path.join(Configuration.OUTPUT_PATH, safe_filename)
            
            try:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(full_text)
               
            except Exception as e:
                print(f"Ошибка при сохранении файла {safe_filename}: {e}")

if __name__ == "__main__":
    main()
