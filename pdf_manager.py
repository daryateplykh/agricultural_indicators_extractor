import os
from config import Configuration
from scan_extractor_mistral import ScannedExtractorMistral
from PIL import Image, ImageEnhance


def preprocess_image(image: Image.Image) -> Image.Image:
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    image = image.convert('L')
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    image = image.point(lambda x: 0 if x < 180 else 255, '1')
    return image


def process_all_pdfs():
    docs = []
    for fname in os.listdir(Configuration.DATA_PATH):
        path = os.path.join(Configuration.DATA_PATH, fname)
        docs.extend(ScannedExtractorMistral()._process_single_pdf(path, fname))
      
    return docs
