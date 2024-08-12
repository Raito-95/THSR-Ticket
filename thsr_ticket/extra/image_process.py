import ddddocr

ocr = ddddocr.DdddOcr(show_ad=False)


def verify_code(image):
    return ocr.classification(image)
