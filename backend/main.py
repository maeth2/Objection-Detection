import asyncio
import base64
import cv2
import io
import numpy as np
import time
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from object_detector import ObjectDetector
from text_detector import TextDetector
from PIL import Image

MAX_REQUESTS = 5 #Maximum Request Queue Size

app = FastAPI()

#Initialise Web Server Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Start Object and Text Detection
det : ObjectDetector = ObjectDetector("yolov8n-oiv7")
det_text : TextDetector = TextDetector(lang='en')

''' 
Receive Data from websocket

@param websocket:         Websocket Connection
@param queue:             Request Queue 
'''
async def receive(websocket : WebSocket, queue : asyncio.Queue) -> None:
    bytes = await websocket.receive_bytes()
    data = np.frombuffer(bytes, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    try:
        queue.put_nowait(img)
    except asyncio.QueueFull:
        pass

'''
Main Object Detection Loop

@param websocket           Websocket Connection
@param queue               Request Queue
'''
async def detectObjects(websocket : WebSocket, queue : asyncio.Queue) -> None:
    lastTime = 0
    
    while True:
        # currentTime = time.time() * 1000
        # timeElasped = currentTime - lastTime
        # lastTime = currentTime
        # print(f"Time Elapsed: {timeElasped} ms")

        img = await queue.get()
        boxes = det.detect(img)
        try:
            await websocket.send_json(jsonable_encoder(boxes))
        except WebSocketDisconnect:
            pass
        except RuntimeError:
            pass

'''
Websocket Initialization

@param websocket            Websocket Connection
'''
@app.websocket("/detect")
async def detect(websocket : WebSocket) -> None:
    await websocket.accept()
    print(websocket.client.host)
    queue : asyncio.Queue = asyncio.Queue(maxsize=MAX_REQUESTS)
    detect_task : asyncio.Task = asyncio.create_task(detectObjects(websocket=websocket, queue=queue)) 
    try:
        while True:
            await receive(websocket, queue)
    except WebSocketDisconnect:
        print("WEBSOCKET DISCONNECTED")
        detect_task.cancel()

'''
Text Detection HTTP Request

@param request              HTTP Request
'''
@app.post("/detect_text")
async def detect_text(request : Request) -> dict:
    byte_data = await request.body()
    byte_data = byte_data.decode('utf-8').split("base64,", 1)[1].encode('utf-8')
    data = base64.b64decode(byte_data)
    img = np.array(Image.open(io.BytesIO(data)).convert('RGB'))
    detect_img = np.array(Image.open(io.BytesIO(data)).convert('RGB'))[:, :, ::-1].copy()
    detection = det.detect(detect_img, detect_color=True)
    text = await det_text.check_image(img)
    if not len(detection) == 0:
        return {"text" : text, "detect" : jsonable_encoder(detection)} 
    return {"text" : "No Objects Detected", "detect" : []}