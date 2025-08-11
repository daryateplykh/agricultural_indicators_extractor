from PIL import Image, ImageEnhance
import numpy as np
import cv2
from typing import Tuple

def preprocess_image(image: Image.Image) -> Image.Image:

    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)

    if image.mode != 'RGB':
        image = image.convert('RGB')

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    return image 

def trim_margins(image: Image.Image, pad: int = 5) -> Image.Image:
    img_array = np.array(image)
    
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    inv = cv2.bitwise_not(gray)
    _, bin_img = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    rows = np.where(bin_img.sum(axis=1) > 0)[0]
    cols = np.where(bin_img.sum(axis=0) > 0)[0]
    
    if len(rows) == 0 or len(cols) == 0:
        return image
    
    top, bottom = max(rows[0] - pad, 0), min(rows[-1] + pad, img_array.shape[0] - 1)
    left, right = max(cols[0] - pad, 0), min(cols[-1] + pad, img_array.shape[1] - 1)
    
    cropped_array = img_array[top:bottom + 1, left:right + 1]
    
    if len(cropped_array.shape) == 3:
        return Image.fromarray(cropped_array)
    else:
        return Image.fromarray(cropped_array, mode='L').convert('RGB')

def find_valley_split_x(image: Image.Image) -> Tuple[int, str]:
    img_array = np.array(image)
    
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    h, w = gray.shape
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

def split_columns(image: Image.Image, split_x: int) -> Tuple[Image.Image, Image.Image]:
    img_array = np.array(image)
    h, w = img_array.shape[:2]
    
    split_x = int(np.clip(split_x, int(w * 0.15), int(w * 0.85)))
    
    left_img_array = img_array[:, :split_x]
    right_img_array = img_array[:, split_x:]
    
    left_img = Image.fromarray(left_img_array)
    right_img = Image.fromarray(right_img_array)
    
    return left_img, right_img

def smart_split_page(image: Image.Image) -> Tuple[Image.Image, Image.Image]:
    trimmed_image = trim_margins(image)
    
    split_x, _ = find_valley_split_x(trimmed_image)
    
    left_column, right_column = split_columns(trimmed_image, split_x)
    
    return left_column, right_column

def split_image_in_half(image: Image.Image) -> Tuple[Image.Image, Image.Image]:
    width, height = image.size
    midpoint = width // 2
    
    left_half = image.crop((0, 0, midpoint, height))
    right_half = image.crop((midpoint, 0, width, height))
    
    return left_half, right_half 