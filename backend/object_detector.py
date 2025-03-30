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

USE_ULTRALYTICS = True

class ObjectDetector():
    def __init__(self, model : str):
        print("INITIALIZING OBJECT DETECTOR")
        if USE_ULTRALYTICS:
            self.model = YOLO(MODEL_PATH + model + ".onnx")
        else:
            self.model = cv2.dnn.readNetFromONNX(MODEL_PATH + model + ".onnx")
        self.color_detect = ColorDetector()
        print("INITIALIZED.")

    def detect(self, frame : cv2.typing.MatLike, detect_color=False):
        result = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)[0]

        bounds : list[dict] = []
        for i in result.boxes:
            coords = i.xyxy[0]
            label = i.cls[0]
            conf = float(i.conf[0].numpy())
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
    
    def detect_beta(self, frame : cv2.typing.MatLike, detect_color=False):        
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (INPUT_WIDTH, INPUT_HEIGHT), (0,0,0), swapRB=True, crop=False)
        self.model.setInput(blob)
        output = self.model.forward()
        output = output.transpose((0, 2, 1))
        rows = output[0].shape[0]

        image_height, image_width, _ = frame.shape
        x_factor = image_width / INPUT_WIDTH
        y_factor = image_height / INPUT_HEIGHT

        bounds : list[dict] = []

        rows = output[0].shape[0]

        detection_boxes = []

        for i in range(rows):
            row = output[0][i]
            conf = row[4]
            classes_score = row[4:]
            _,_,_, max_idx = cv2.minMaxLoc(classes_score)
            class_id = max_idx[1]
            
            x, y, w, h = row[0:4]
            if classes_score[class_id] > CONFIDENCE_THRESHOLD:
                coords = [(x - w/2) * x_factor, (y - h/2) * y_factor, (x + w/2) * x_factor, (y + h/2) * y_factor]
                label = class_id
                conf = row[4]

                b = BoundingBox(
                    color=(255, 0, 0), 
                    thickness=2, 
                    label=helper.yolo_classes[int(label)]
                ).set_bounds_tl_br((coords[0], coords[1]), (coords[2], coords[3]))

                found = False
                for box in detection_boxes:
                    if b.check_intersection(box) and b.label == box.label: 
                        found = True
                        break

                if not found:
                    if DEBUG: b.render(frame)
                    if detect_color:
                        color = self.color_detect.detect(frame, (b.bounds[0], b.bounds[1]), (b.bounds[2], b.bounds[3]))
                        b.label = f"{color} {b.label}"
                    bounds.append({"bounds" : b.bounds, "label" : b.label, "confidence"  : 0})
                    detection_boxes.append(b)
        
        if DEBUG:
            cv2.imshow('test', frame)
            if cv2.waitKey(10) == 27 or not cv2.getWindowProperty('test', cv2.WND_PROP_VISIBLE):
                cv2.destroyAllWindows()

        return bounds
    
# img = cv2.imread("./test images/us.png")
# detect = ObjectDetector("yolov8m-oiv7")
# detect.detect_ultralytics(frame=img)