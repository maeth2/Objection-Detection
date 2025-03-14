import asyncio
import base64
import cv2
import io
import numpy as np
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from object_detector import ObjectDetector
from text_detector import TextDetector
from PIL import Image, ImageFilter

MAX_REQUESTS = 3

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
det_text : TextDetector = TextDetector(lang='en')

async def receive(websocket : WebSocket, queue : asyncio.Queue) -> None:
    bytes = await websocket.receive_bytes()
    data = np.frombuffer(bytes, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    try:
        queue.put_nowait(img)
    except asyncio.QueueFull:
         pass

async def detectObjects(websocket : WebSocket, queue : asyncio.Queue) -> None:
    while True:
        img = await queue.get()
        boxes = det.detect(img, img.shape[1], img.shape[0])
        try:
            await websocket.send_json(jsonable_encoder(boxes))
        except WebSocketDisconnect:
            pass
        except RuntimeError:
            pass
        
@app.websocket("/detect")
async def detect(websocket : WebSocket) -> None:
    await websocket.accept()
    queue : asyncio.Queue = asyncio.Queue(maxsize=MAX_REQUESTS)
    detect_task : asyncio.Task = asyncio.create_task(detectObjects(websocket=websocket, queue=queue)) 
    try:
        while True:
            await receive(websocket, queue)
    except WebSocketDisconnect:
        print("WEBSOCKET DISCONNECTED")
        detect_task.cancel()
        
@app.post("/detect_text")
async def detect_text(request : Request) -> dict:
    byte_data = await request.body()
    byte_data = byte_data.decode('utf-8').split("base64,", 1)[1].encode('utf-8')
    data = base64.b64decode(byte_data)
    img = np.array(Image.open(io.BytesIO(data)).convert('RGB'))
    detect_img = np.array(Image.open(io.BytesIO(data)).convert('RGB'))[:, :, ::-1].copy()
    detection = det.detect(detect_img, img.shape[1], img.shape[0], detect_color=True)
    text = await det_text.check_image(img)
    if not len(detection) == 0:
        print("HELLO ", detection)
        return {"text" : text, "detect" : jsonable_encoder(detection)} 
    return {"text" : "No Objects Detected", "detect" : []}