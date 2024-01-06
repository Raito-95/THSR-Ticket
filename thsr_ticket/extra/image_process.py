import ddddocr

ocr = ddddocr.DdddOcr()

def verify_code(image):
    result = ocr.classification(image)
    return result