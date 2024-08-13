import ddddocr
from PIL import Image

ocr = ddddocr.DdddOcr(show_ad=False)

def verify_code(image: Image.Image) -> str:
    result = ocr.classification(image)
    
    if isinstance(result, str):
        return result
    elif isinstance(result, dict):
        return ''.join(result.get('charsets', []))
    else:
        return ""