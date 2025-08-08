from PIL import Image, ImageEnhance

def preprocess_image(image: Image.Image) -> Image.Image:

    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)

    if image.mode != 'RGB':
        image = image.convert('RGB')

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    return image 