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

def get_binary_projection(image: Image.Image, dilation_kernel_size=(40, 1)):
    img_array = np.array(image)
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    _, bin_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    if dilation_kernel_size:
        kernel = np.ones(dilation_kernel_size, np.uint8)
        bin_img = cv2.dilate(bin_img, kernel, iterations=1)
        
    return bin_img

def find_equal_area_split_x(bin_img: np.ndarray) -> int:
    proj = bin_img.sum(axis=0).astype(np.float32)
    cum_sum = np.cumsum(proj)
    total_sum = cum_sum[-1]
    
    diff = np.abs(cum_sum - (total_sum - cum_sum))
    split_x = np.argmin(diff)
    
    return split_x

def validate_split_corridor(bin_img: np.ndarray, split_x: int, width: int, height: int, corridor_width=10, threshold=0.05, coverage=0.7) -> bool:
    start_x = max(0, split_x - corridor_width // 2)
    end_x = min(width, split_x + corridor_width // 2)
    
    corridor = bin_img[:, start_x:end_x]
    
    ignore_margin = int(height * 0.1)
    corridor_core = corridor[ignore_margin:-ignore_margin, :]
    
    if corridor_core.size == 0:
        return False
        
    vertical_occupancy = corridor_core.sum(axis=1) / (255.0 * corridor_core.shape[1])
    empty_lines = np.sum(vertical_occupancy < threshold)
    
    return (empty_lines / corridor_core.shape[0]) >= coverage

def find_best_split_x(image: Image.Image) -> int:
    h, w = image.height, image.width
    bin_img = get_binary_projection(image, dilation_kernel_size=(w // 50, 1))

    x0 = find_equal_area_split_x(bin_img)

    search_window_width = int(w * 0.1)
    search_start = max(0, x0 - search_window_width)
    search_end = min(w, x0 + search_window_width)

    raw_bin_img = get_binary_projection(image, dilation_kernel_size=None)
    proj = raw_bin_img[:, search_start:search_end].sum(axis=0)

    if proj.size == 0:
        return x0

    local_min_x = np.argmin(proj) + search_start

    if validate_split_corridor(raw_bin_img, local_min_x, w, h):
        return local_min_x
    else:
        return x0

def split_columns(image: Image.Image, split_x: int) -> Tuple[Image.Image, Image.Image]:
    img_array = np.array(image)
    h, w = img_array.shape[:2]

    dpi = 200 
    overlap_px = int((0.5 / 2.54) * dpi)

    split_x = int(np.clip(split_x, int(w * 0.15), int(w * 0.85)))
    
    left_end = min(split_x + overlap_px, w)
    right_start = max(split_x - overlap_px, 0)

    left_img_array = img_array[:, :left_end]
    right_img_array = img_array[:, right_start:]
    
    left_img = Image.fromarray(left_img_array)
    right_img = Image.fromarray(right_img_array)
    
    return left_img, right_img

def smart_split_page(image: Image.Image) -> Tuple[Image.Image, Image.Image]:
    trimmed_image = trim_margins(image)
    w, h = trimmed_image.size

    split_x = find_best_split_x(trimmed_image)

    if split_x < (w * 0.4):
        dpi = 200
        extra_width_px = int((2.0 / 2.54) * dpi)
        new_split_x = split_x + extra_width_px
        split_x = min(new_split_x, w)
        
    left_column, right_column = split_columns(trimmed_image, split_x)
    return left_column, right_column

def split_image_in_half(image: Image.Image) -> Tuple[Image.Image, Image.Image]:
    width, height = image.size
    midpoint = width // 2
    
    dpi = 200
    overlap_px = int((0.5 / 2.54) * dpi)

    left_end = min(midpoint + overlap_px, width)
    right_start = max(midpoint - overlap_px, 0)
    
    left_half = image.crop((0, 0, left_end, height))
    right_half = image.crop((right_start, 0, width, height))
    
    return left_half, right_half

def split_image_horizontally(image: Image.Image) -> Tuple[Image.Image, Image.Image]:
    width, height = image.size
    midpoint = height // 2
    top_half = image.crop((0, 0, width, midpoint))
    bottom_half = image.crop((0, midpoint, width, height))
    return top_half, bottom_half 