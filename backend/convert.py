from ultralytics import YOLO

model = "yolov8m-oiv7"

nm = YOLO("./models/" + model + ".pt")
nm.export(format="onnx", imgsz=[640,640], opset=12)

print("SUCESSFUL")