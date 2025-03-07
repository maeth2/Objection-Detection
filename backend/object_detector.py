import cv2
import helper
from ultralytics import YOLO
from bounding_boxes import BoundingBox

CONFIDENCE_THRESHOLD = 0.1
INTERSECTION_THRESHOLD = 0.7

class ObjectDetector():
    def click_event(self, event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(x, y)
    
    def __init__(self, model):
        print("INITIALIZING OBJECT DETECTOR")
        self.model = YOLO(model)
        print("INITIALIZED.")

    def detect(self, frame, frame_width, frame_height, display=False):
        bounding_box = BoundingBox(frame_width / 2, frame_height / 2, 200, 200)
        result = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)[0]

        bounds : list[dict] = []
        for i in result.boxes:
            coords = i.xyxy[0]
            label = i.cls[0]
            b = BoundingBox(
                color=(255, 255, 255), 
                thickness=1, 
                label=helper.yolo_classes[int(label)]
            ).set_bounds_tl_br((coords[0], coords[1]), (coords[2], coords[3]))
            if b.check_intersection(bounding_box):
                if display: b.render(frame)
                bounds.append({"bounds" : b.bounds, "label" : b.label, "confidence"  : i.conf[0]})
        
        if display:
            cv2.imshow('test', frame)
            if cv2.waitKey(10) == 27 or not cv2.getWindowProperty('test', cv2.WND_PROP_VISIBLE):
                        cv2.destroyAllWindows()


        return bounds

        