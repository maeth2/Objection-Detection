import cv2
import helper
from ultralytics import YOLO

CONFIDENCE_THRESHOLD = 0.05
INTERSECTION_THRESHOLD = 0.7

class BoundingBox():
    def __init__(self, x=0, y=0, width=0, height=0, thickness=3, color=(0, 0, 0),scaling=(1, 1), label=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.thickness = thickness
        self.color = color
        self.scaling = scaling
        self.update_bounds()
    
    def set_bounds_from_coords(self, tl, br):
        self.x = (tl[0] + br[0]) / 2
        self.y = (tl[1] + br[1]) / 2
        self.width = tl[0] - br[0]
        self.height = tl[1] - br[1]
        self.bounds = self.update_bounds()
        return self

    def resize(self, width, height):
        self.width = width
        self.height = height
        self.update_bounds()
    
    def set_pos(self, x, y):
        self.x = x
        self.y = y
        self.update_bounds()
    
    def update_bounds(self):
        self.bounds = [
            int((self.x - self.width / 2) * self.scaling[0]), 
            int((self.y - self.height / 2) * self.scaling[1]), 
            int((self.x + self.width / 2) * self.scaling[0]), 
            int((self.y + self.height / 2) * self.scaling[1])
        ]
        return self.bounds
    
    def get_bounds(self):
        return self.bounds
    
    def check_intersection(self, b):
        box : BoundingBox = b
        if self.x > box.bounds[0] and self.x < box.bounds[2] and self.y > box.bounds[1] and self.y < box.bounds[3]:
            return True
        return False
    
    def check_area_of_intersection(self, b):
        box : BoundingBox = b
        x1 = max(self.bounds[0] - box.bounds[0])
        y1 = max(self.bounds[1] - box.bounds[1])
        x2 = max(self.bounds[2] - box.bounds[2])
        y2 = max(self.bounds[3] - box.bounds[3])

        return (x2 - x1) * (y2 - y1)
    
    def check_area_of_union(self, b):
        box : BoundingBox = b
        bx1 = (self.bounds[2] - self.bounds[0]) * (self.bounds[3] - self.bounds[1])
        bx2 = (box[2] - box[0]) * (box[3] - box[1])
        return bx1 + bx2
    
    def check_area_of_inter_union(self, b):
        aoi = self.check_area_of_intersection(b)
        aou = self.check_area_of_union(b)
        return aoi / (aou - aoi)

class ObjectDetector():
    def click_event(self, event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(x, y)
    
    def __init__(self, model):
        print("INITIALIZING OBJECT DETECTOR")
        self.model = YOLO(model)
        print("INITIALIZED.")

    def detect(self, frame, frame_width, frame_height):
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
            ).set_bounds_from_coords((coords[2], coords[3]), (coords[0], coords[1]))
            if b.check_intersection(bounding_box):
                bounds.append({"bounds" : b.bounds, "label" : b.label, "confidence"  : i.conf[0]})

        return bounds

        