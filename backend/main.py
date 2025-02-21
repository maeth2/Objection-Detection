import base64
import cv2
import io
import numpy as np
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from object_detector import ObjectDetector
from PIL import Image

DEBUG_MODE = False

app = FastAPI()

origins = [
    "http://127.0.0.1:8080",
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

det : ObjectDetector = ObjectDetector("./models/yolov8n-oiv7.onnx")

async def show_boxes(frame, boxes : list[dict]):
    for i in boxes:
        bounds = i["bounds"]
        cv2.putText(frame, text=i["label"], org=(bounds[2], bounds[3]), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(255, 255, 255), thickness=1, lineType=cv2.LINE_AA)
        cv2.rectangle(frame, pt1=(bounds[0], bounds[1]), pt2=(bounds[2], bounds[3]), color=(255, 255, 255), thickness=1)
    
    cv2.imshow('test', frame)
    if cv2.waitKey(10) == 27 or not cv2.getWindowProperty('test', cv2.WND_PROP_VISIBLE):
                cv2.destroyAllWindows()

async def receive(websocket : WebSocket) -> cv2.typing.MatLike:
    bytes = await websocket.receive_bytes()
    data = np.frombuffer(bytes, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    return img

@app.websocket("/detect")
async def detect(websocket : WebSocket):
    await websocket.accept()
    while True:
        try:
            img = await receive(websocket)
            boxes = det.detect(img, img.shape[1], img.shape[0])
            if DEBUG_MODE: 
                await show_boxes(img, boxes)
            await websocket.send_json(jsonable_encoder(boxes))
        except WebSocketDisconnect:
            await websocket.close()
        
@app.post("/test")
async def test(request : Request) -> dict:
    byte_data = await request.body()
    byte_data = byte_data.decode('utf-8').split("base64,", 1)[1].encode('utf-8')
    data = base64.b64decode(byte_data)
    img = cv2.cvtColor(np.array(Image.open(io.BytesIO(data))), cv2.COLOR_RGB2BGR)
    boxes = det.detect(img, img.shape[1], img.shape[0])
    cv2.imshow('test', img)
    if cv2.waitKey(30) == 27 or not cv2.getWindowProperty('test', cv2.WND_PROP_VISIBLE):
        cv2.destroyAllWindows()
    return {"Boxes" : boxes}