document.body.onload = function(){init()}
const SHOW_LOGS = false;
const DETECTION_WEBSOCKET_ADDRESS = 'ws://127.0.0.1:8000/detect';
const CAMERA_WEBSOCKET_ADDRESS = 'ws://172.20.10.9:80/ws'
const RETRY_INTERVAL = 1000;
const LABEL_RESOLUTION = 2;
const WEBCAM = true;
const FPS = 60, FPS_DETECT = 5;
var websocketConnected = false;
var inputCanvas, inputContext, outputCanvas, outputContext;
var webCamToggle = true;
var wsDetect, wsDetectRetry, wsCamera, wsCameraRetry;

function init(){
    console.log("INITIALIZING");
    inputCanvas = document.getElementById("input");
    inputContext = inputCanvas.getContext("2d");
    outputCanvas = document.getElementById("output");
    outputContext = outputCanvas.getContext("2d");
    labelCanvas = document.getElementById("labels");
    labelContext = labelCanvas.getContext("2d");
    labelCanvas.width = labelCanvas.width * LABEL_RESOLUTION;
    labelCanvas.height = labelCanvas.height * LABEL_RESOLUTION;
    connectDetectionWS();
    connectCameraWS();
}

const webcam = document.createElement('video');
startWebCam(webcam)

function startWebCam(webcam){
    const contraints = {
        video : {
            facingMode : 'enviroment'
        }
    }
    navigator.mediaDevices.getUserMedia(contraints).then((stream) => {
        webcam.srcObject = stream;
        webcam.play();
        setInterval(() =>{
            if(WEBCAM){
                inputContext.clearRect(0, 0, inputCanvas.width, inputCanvas.height);
                inputContext.drawImage(webcam, 0, 0, inputCanvas.width, inputCanvas.height);
            }
        }, 1000 / FPS);
    }).catch((error) =>{
        console.error(error);
    });
}

function stopWebCam(webcam){
    webcam.srcObject.getTracks().forEach((track) => {track.stop()});
}

Array.from(document.getElementsByClassName("video")).forEach((button) => button.addEventListener('click', () => {
    if(!webCamToggle){
        startWebCam(webcam);
        webCamToggle = true;
    }else{
        stopWebCam(webcam);
        webCamToggle = false;
    }
    document.getElementById("video_on").style.display = webCamToggle ? 'block' : 'none';
    document.getElementById("output").style.display = webCamToggle ? 'block' : 'none';
    document.getElementById("video_off").style.display = !webCamToggle ? 'block' : 'none';
}));

document.getElementsByClassName("camera")[0].addEventListener('click', httpImgToText);

function connectDetectionWS(){
    console.log("ATTEMPTING CONNECTION TO: ", DETECTION_WEBSOCKET_ADDRESS);
    wsDetect = new WebSocket(DETECTION_WEBSOCKET_ADDRESS);
    wsDetect.addEventListener('message', (event) => {
        outputContext.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
        labelContext.clearRect(0, 0, labelCanvas.width, labelCanvas.height);
        boxes = JSON.parse(event.data);
        if(SHOW_LOGS) console.table(boxes);
        boxes.forEach(box => {
            var width = box['bounds'][2] - box['bounds'][0];
            var height = box['bounds'][3] - box['bounds'][1];
            outputContext.beginPath();
            outputContext.strokeStyle = "red";
            outputContext.lineWidth = 1;
            outputContext.rect(box['bounds'][0], box['bounds'][1], width, height);
            outputContext.stroke();

            labelContext.font = '10px Arial';
            labelContext.textAlign ='left';
            labelContext.textBaseline = 'bottom';
            labelContext.fillStyle = "#05f2fa";
            labelContext.fillText(box['label'], box['bounds'][0] * LABEL_RESOLUTION, box['bounds'][1] * LABEL_RESOLUTION);
        });
    });
    wsDetect.addEventListener('open', (event) => {
        websocketConnected = true;
        clearInterval(wsDetectRetry);
        console.log("CONNECTED TO: ", DETECTION_WEBSOCKET_ADDRESS);
    });
    wsDetect.addEventListener('close', (event) => {
        console.log("DISCONNECTED");
        websocketConnected = false;
        outputContext.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
        clearInterval(wsDetectRetry);
        wsDetectRetry = setInterval(() => {
            console.log("RETRYING CONNECTION...");
            connectDetectionWS();
        }, RETRY_INTERVAL);
    });
}

function connectCameraWS(){
    console.log("ATTEMPTING CONNECTION TO: ", CAMERA_WEBSOCKET_ADDRESS);
    wsCamera = new WebSocket(CAMERA_WEBSOCKET_ADDRESS);
    console.log("SUCESSFULLY CONNECTED TO: ", CAMERA_WEBSOCKET_ADDRESS);
    wsCamera.addEventListener('message', (event) => {
        if (!WEBCAM){
            var blob = event.data;
            var img = new Image();
            img.onload = function() {
                inputContext.clearRect(0, 0, inputCanvas.width, inputCanvas.height);
                inputContext.drawImage(img, 0, 0, inputCanvas.width, inputCanvas.height)
            }
            img.src = URL.createObjectURL(blob);
        }
    });
}

setInterval(() => {
    if(websocketConnected && webCamToggle){
        if(SHOW_LOGS) console.log("Sending Web Socket Request...");
        inputCanvas.toBlob((blob) =>{wsDetect.send(blob)}, 'image/png');
    }
}, 1000 / FPS_DETECT);

// setInterval(() => {
//     wsCamera.send("HI THERE.");
// }, 1000 / FPS_DETECT);

async function httpImgToText(){
    inputContext.drawImage(webcam, 0, 0, inputCanvas.width, inputCanvas.height);
    const data = inputCanvas.toDataURL("image/jpeg", 1.0);
    await fetch(URL="http://127.0.0.1:8000/detect_text", {
        method : 'POST',
        body : data
    }).then((response) => {
        response.json().then((response_json) => {
            console.log(response_json['text']);
        });
    }).catch((error) => {
        console.log(error);
    });
}