import cv2
import helper
from ultralytics import YOLO
from bounding_boxes import BoundingBox
import numpy as np
from color_detector import ColorDetector

DEBUG = False
CONFIDENCE_THRESHOLD = 0.2

class ObjectDetector():
    def __init__(self, model : str):
        print("INITIALIZING OBJECT DETECTOR")
        self.model = YOLO(model)
        self.color_detect = ColorDetector()
        print("INITIALIZED.")

    def detect(self, frame : cv2.typing.MatLike, frame_width : float, frame_height : float, detect_color=False):
        bounding_box = BoundingBox(frame_width / 2, frame_height / 2, frame_width * 0.5, frame_height * 0.5)
        result = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)[0]

        bounds : list[dict] = [{"bounds" : bounding_box.bounds, "label" : "Detection Box", "confidence"  : 0}]
        for i in result.boxes:
            coords = i.xyxy[0]
            label = i.cls[0]
            conf = float(i.conf[0].numpy())
            b = BoundingBox(
                color=(255, 255, 255), 
                thickness=1, 
                label=helper.yolo_classes[int(label)]
            ).set_bounds_tl_br((coords[0], coords[1]), (coords[2], coords[3]))
            if b.check_intersection(bounding_box):
                if DEBUG: b.render(frame)
                if detect_color:
                    color = self.color_detect.detect(frame, (b.bounds[0], b.bounds[1]), (b.bounds[2], b.bounds[3]))
                    b.label = f"{color} {b.label}"
                bounds.append({"bounds" : b.bounds, "label" : b.label, "confidence"  : conf})
        
        if DEBUG:
            cv2.imshow('test', frame)
            if cv2.waitKey(10) == 27 or not cv2.getWindowProperty('test', cv2.WND_PROP_VISIBLE):
                        cv2.destroyAllWindows()

        return bounds

        