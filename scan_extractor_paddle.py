import os
import re
import argparse
import shutil
from typing import List, Tuple
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
            img_rgb = np.array(pil_img)
            img_rgb = trim_margins(img_rgb)
            split_x, _ = find_valley_split_x(img_rgb)
            left_img, right_img = split_columns(img_rgb, split_x)
            left_text = extract_text_safe(ocr, left_img)
            right_text = extract_text_safe(ocr, right_img)
            combo_text = (left_text.strip() + "\n" + right_text.strip()).strip()
            out_txt = os.path.join(args.out_text, f"{safe_name(stem)}_page{page_idx}.txt")
            try:
                with open(out_txt, "w", encoding="utf-8") as f:
                    f.write(combo_text)
            except Exception:
                pass

def trim_margins(img: np.ndarray, pad: int = 5) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    inv = cv2.bitwise_not(gray)
    _, bin_img = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    rows = np.where(bin_img.sum(axis=1) > 0)[0]
    cols = np.where(bin_img.sum(axis=0) > 0)[0]
    if len(rows) == 0 or len(cols) == 0:
        return img
    top, bottom = max(rows[0] - pad, 0), min(rows[-1] + pad, img.shape[0] - 1)
    left, right = max(cols[0] - pad, 0), min(cols[-1] + pad, img.shape[1] - 1)
    return img[top:bottom + 1, left:right + 1]

def find_valley_split_x(img_rgb: np.ndarray) -> Tuple[int, str]:
    h, w = img_rgb.shape[:2]
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.medianBlur(gray, 3)
    inv = cv2.bitwise_not(gray)
    _, bin_img = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    proj = bin_img.sum(axis=0).astype(np.float32)
    k = max(11, w // 100 * 2 + 1)
    proj_smooth = cv2.blur(proj.reshape(1, -1), (k, 1)).flatten()
    left_bound = int(w * 0.25)
    right_bound = int(w * 0.75)
    central = proj_smooth[left_bound:right_bound]
    if central.size == 0:
        return w // 2, ""
    min_idx = int(np.argmin(central)) + left_bound
    valley = proj_smooth[min_idx]
    mean_central = float(np.mean(central))
    if valley < mean_central * 0.6:
        return min_idx, ""
    else:
        return w // 2, ""

def split_columns(image: np.ndarray, split_x: int) -> Tuple[np.ndarray, np.ndarray]:
    h, w = image.shape[:2]
    split_x = int(np.clip(split_x, int(w * 0.15), int(w * 0.85)))
    left_img = image[:, :split_x]
    right_img = image[:, split_x:]
    return left_img, right_img

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

