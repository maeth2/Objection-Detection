import cv2
import helper
from bounding_boxes import BoundingBox
from color_detector import ColorDetector
from ultralytics import YOLO

MODEL_PATH = "./models/"
DEBUG = False
CONFIDENCE_THRESHOLD = 0.2
INPUT_WIDTH = 640
INPUT_HEIGHT = 640

class ObjectDetector():
    def __init__(self, model : str):
        print("INITIALIZING OBJECT DETECTOR")
        try:
            self.model = YOLO(MODEL_PATH + model + ".engine")
        except FileNotFoundError:
            nm = YOLO("./models/" + model + ".pt")
            self.model = YOLO(nm.export(format="engine"))
        self.color_detect = ColorDetector()
        print("INITIALIZED.")

    def detect(self, frame : cv2.typing.MatLike, detect_color=False):
        result = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)[0]

        bounds : list[dict] = []
        for i in result.boxes:
            coords = i.xyxy[0]
            label = i.cls[0]
            conf = 0
            b = BoundingBox(
                color=(255, 255, 255), 
                thickness=1, 
                label=helper.yolo_classes[int(label)]
            ).set_bounds_tl_br((coords[0], coords[1]), (coords[2], coords[3]))
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
    
# img = cv2.imread("./test images/us.png")
# detect = ObjectDetector("yolov8m-oiv7")
# detect.detect_ultralytics(frame=img)