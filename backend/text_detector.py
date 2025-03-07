import easyocr
import numpy as np
import bounding_boxes
from bounding_boxes import BoundingBox
import cv2
from PIL import Image

DEBUG = True
CONFIDENCE_THRESHOLD = 0.75
class TextDetector():
    def __init__(self, lang : str):
        print("INITIALIZING TEXT DETECTOR")
        self.reader = easyocr.Reader([lang], gpu=True)

    async def check_image(self, img : np.array) -> list[BoundingBox]:
        print("CHECKING IMAGE")

        text = self.reader.readtext(image=img, batch_size=5, text_threshold=CONFIDENCE_THRESHOLD)
        found_text : list[BoundingBox] = []
        
        for bounds, text, conf in text:
            b = BoundingBox(label=text).set_bounds_tl_br((bounds[0][0], bounds[0][1]), (bounds[2][0], bounds[2][1]))
            found_text.append(b)
        
        sorted_text = bounding_boxes.sort_boxes(found_text, y_threshold=10)
        grouped_text = bounding_boxes.group_boxes(sorted_text, x_threshold=5, y_threshold=6)

        output : list[str] = []
        for i in grouped_text:
            for j in i:
                output.append(j.label)
        
        if DEBUG:
            image = img[:, :, ::-1].copy()
            for i in grouped_text:
                for j in i:
                    j.render(frame=image, label=True, color=(255, 0, 0), thickness=2)
            cv2.imshow("test", image)
            if cv2.waitKey(0) == 27 or not cv2.getWindowProperty('test', cv2.WND_PROP_VISIBLE):
                cv2.destroyAllWindows()

        return output

# txt = TextDetector('en')
# file = "stop.png"
# img = Image.open(f"./test images/{file}").convert('RGB')

# text : list[BoundingBox] = txt.check_image(np.array(img))