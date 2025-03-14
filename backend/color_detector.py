import cv2
# from object_detector import ObjectDetector
import numpy as np

DEBUG = False

hsv_colors = [
    ["red", 0, 16],
    ["orange", 17, 50], 
    ["yellow", 51, 65] ,
    ["green", 66, 140] ,
    ["blue", 141, 240],
    ["purple", 241, 275],
    ["pink", 276, 335],
    ["red", 336, 359] 
]

hsv_shades = [
    ["black", 0, 40],
    ["white", 41, 100] 
]

class ColorDetector:
    def detect(self, img : cv2.typing.MatLike, tl, br) -> str:
        obj = img[tl[1] : br[1], tl[0] : br[0]]
        hsv = cv2.cvtColor(obj, cv2.COLOR_BGR2HSV)

        mx = -1
        mx_color = ""
        mx_mask = ""
        
        for i in hsv_colors:
            mask = cv2.inRange(hsv, np.array([i[1] / 2, 50, 0]), np.array([i[2] / 2, 255, 255]))
            percent = (mask > 0).mean() * 100
            if percent > mx:
                mx = percent
                mx_color = i[0]
                mx_mask = mask

        for i in hsv_shades:
            mask = cv2.inRange(hsv, np.array([0, 0, i[1]]), np.array([179, 49, i[2]]))
            percent = (mask > 0).mean() * 100
            if percent > mx:
                mx = percent
                mx_color = i[0]
                mx_mask = mask
        
        if DEBUG:
            cv2.imshow('test', mx_mask)
            if cv2.waitKey(0) == 27 or not cv2.getWindowProperty('test', cv2.WND_PROP_VISIBLE):
                cv2.destroyAllWindows()

        return mx_color

# detect = ObjectDetector("./models/yolov8n-oiv7.onnx")
# img = cv2.imread("./test images/green_bottle.png")
# boxes = detect.detect(img, img.shape[0], img.shape[1])
# color_detect = ColorDetector()
# for i in boxes:
#     bounds = i['bounds']
#     color = color_detect.detect(img, (bounds[0], bounds[1]), (bounds[2], bounds[3]))
#     print(color, i['label'], i['confidence'])