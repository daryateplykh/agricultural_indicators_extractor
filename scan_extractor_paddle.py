import os
import re
import argparse
import shutil
from typing import List
import numpy as np
import cv2
from pdf2image import convert_from_path
from paddleocr import PaddleOCR

DATA_PATH = "data"
OUT_TEXT_DIR = "output_chunks"
DPI_DEFAULT = 200

def main():
    parser = argparse.ArgumentParser(description="PDF -> OCR -> TXT (деление на 2 колонки)")
    parser.add_argument("--data", default=DATA_PATH)
    parser.add_argument("--out_text", default=OUT_TEXT_DIR)
    parser.add_argument("--dpi", type=int, default=DPI_DEFAULT)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if args.reset and os.path.exists(args.out_text):
        shutil.rmtree(args.out_text)

    os.makedirs(args.out_text, exist_ok=True)

    if not os.path.exists(args.data):
        return

    pdf_files = [f for f in os.listdir(args.data) if f.lower().endswith(".pdf")]
    ocr = PaddleOCR(lang="en", use_textline_orientation=True)

    for filename in pdf_files:
        filepath = os.path.join(args.data, filename)
        stem = os.path.splitext(filename)[0]
        try:
            images = convert_from_path(filepath, dpi=args.dpi)
        except Exception:
            continue

        for page_idx, pil_img in enumerate(images, start=1):
            from image_utils import smart_split_page
            left_img, right_img = smart_split_page(pil_img)
            

            left_img_array = np.array(left_img)
            right_img_array = np.array(right_img)
            
            left_text = extract_text_safe(ocr, left_img_array)
            right_text = extract_text_safe(ocr, right_img_array)
            combo_text = (left_text.strip() + "\n" + right_text.strip()).strip()
            out_txt = os.path.join(args.out_text, f"{safe_name(stem)}_page{page_idx}.txt")
            try:
                with open(out_txt, "w", encoding="utf-8") as f:
                    f.write(combo_text)
            except Exception:
                pass



def extract_text_safe(ocr: PaddleOCR, image: np.ndarray) -> str:
    processed = preprocess_for_ocr(image)
    try:
        pred = ocr.predict(processed)
        texts = collect_texts(pred)
        joined = "\n".join(texts).strip()
        if joined:
            return joined
    except Exception:
        pass
    try:
        res = ocr.ocr(processed, use_textline_orientation=True)
        texts = collect_texts(res)
        return "\n".join(texts).strip()
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

def safe_name(s: str) -> str:
    return re.sub(r"[^\w\-]+", "_", s)

if __name__ == "__main__":
    main()

