import re

def clean_ocr_text(text: str) -> str:
    pattern = r'[^a-zA-Z0-9\s.,!?"\'()-]'
    cleaned_text = re.sub(pattern, '', text, flags=re.UNICODE)
    return cleaned_text

def stitch_numbers(text: str) -> str:
    pattern = r'(\d+([ ]\d+)+)'
    
    def replace_spaces(match):
        return match.group(0).replace(' ', '')
        
    return re.sub(pattern, replace_spaces, text)
