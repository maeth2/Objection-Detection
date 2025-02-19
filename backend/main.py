import base64
import cv2
import io
import numpy as np
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from object_detector import ObjectDetector
from PIL import Image


app = FastAPI()

origins = [
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

det : ObjectDetector = ObjectDetector("C:/Users/maeth/Coding/Python/University/1st Year/P3/models/yolov8n-oiv7.onnx")

async def receive(websocket : WebSocket):
    bytes = await websocket.receive_bytes()
    data = np.frombuffer(bytes, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    return image

@app.websocket("/detect")
async def detect(websocket : WebSocket):
    await websocket.accept()
    print("CONNECTED")        
    while True:
        try:
            image = await receive(websocket)
            cv2.imshow('test', image)
            if cv2.waitKey(30) == 27 or not cv2.getWindowProperty('test', cv2.WND_PROP_VISIBLE):
                cv2.destroyAllWindows()
        except WebSocketDisconnect:
            await websocket.close()
        
@app.post("/test")
async def test(request : Request):
    byte_data = await request.body()
    byte_data = byte_data.decode('utf-8').split("base64,", 1)[1].encode('utf-8')
    data = base64.b64decode(byte_data)
    img = cv2.cvtColor(np.array(Image.open(io.BytesIO(data))), cv2.COLOR_RGB2BGR)
    cv2.imshow('test', img)
    if cv2.waitKey(30) == 27 or not cv2.getWindowProperty('test', cv2.WND_PROP_VISIBLE):
        cv2.destroyAllWindows()
    return {"TEST" : "SUCESSFUL"}