import ddddocr

ocr = ddddocr.DdddOcr()


def verify_code(image):
    return ocr.classification(image)
