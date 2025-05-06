import ddddocr
from PIL import Image

ocr = ddddocr.DdddOcr(show_ad=False)


def verify_code(image: Image.Image) -> str:
    if not isinstance(image, Image.Image):
        raise ValueError("Input must be a PIL.Image.Image instance.")

    result = ocr.classification(image)

    if isinstance(result, str):
        return result
    elif isinstance(result, dict):
        return "".join(result.get("charsets", []))
    else:
        print(f"W: Unexpected OCR result type: {type(result)}")
        return ""
