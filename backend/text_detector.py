import easyocr
import numpy as np
from PIL import Image

CONFIDENCE_THRESHOLD = 0.99
class TextDetector():
    def __init__(self, lang : str):
        print("INITIALIZING TEXT DETECTOR")
        self.reader = easyocr.Reader([lang], gpu=True)

    def check_image(self, img : np.array) -> dict:
        text = self.reader.readtext(image=img, batch_size=5)
        found_text = []
        for bounds, txt, score in text:
            if score > CONFIDENCE_THRESHOLD:
                found_text.append([txt, float(score)])
        return found_text

# print("DETECTING")
# txt = TextDetector('en')
# img = Image.open("./tomato.png")
# img.show()
# text = txt.check_image(np.array(img))
# print(text)