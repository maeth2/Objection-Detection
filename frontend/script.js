document.body.onload = function(){init()}
const SHOW_LOGS = false;
const WEBSOCKET_ADDRESS = 'ws://127.0.0.1:8000/detect';
const RETRY_INTERVAL = 10000;
const FPS = 60, FPS_DETECT = 5;
var websocketConnected = false;
var inputCanvas, inputContext, outputCanvas, outputContext;
var ws, wsRetry;

function init(){
    console.log("INITIALIZING");
    inputCanvas = document.getElementById("input");
    inputContext = inputCanvas.getContext("2d");
    outputCanvas = document.getElementById("output");
    outputContext = outputCanvas.getContext("2d");
    connectWS();
}

const webcam = document.createElement('video');
const contraints = {
    video : {
        facingMode : 'enviroment'
    }
}
navigator.mediaDevices.getUserMedia(contraints).then((stream) => {
    webcam.srcObject = stream;
    webcam.play();
    setInterval(() =>{
        inputContext.clearRect(0, 0, inputCanvas.width, inputCanvas.height);
        inputContext.drawImage(webcam, 0, 0, inputCanvas.width, inputCanvas.height);
    }, 1000 / FPS);
}).catch((error) =>{
    console.error(error);
});
webcam.addEventListener('click', httpRequest);

function connectWS(){
    console.log("ATTEMPTING CONNECTION TO: ", WEBSOCKET_ADDRESS);
    ws = new WebSocket(WEBSOCKET_ADDRESS);
    ws.addEventListener('message', (event) => {
        outputContext.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
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

            outputContext.font = '5px Arial';
            outputContext.textAlign ='left';
            outputContext.textBaseline = 'bottom';
            outputContext.fillStyle = "black";   
            outputContext.fillText(box['label'], box['bounds'][0], box['bounds'][1]);
        });
    });
    ws.addEventListener('open', (event) => {
        websocketConnected = true;
        clearInterval(wsRetry)
        console.log("CONNECTED TO: ", WEBSOCKET_ADDRESS);
    });
    ws.addEventListener('close', (event) => {
        websocketConnected = false
        outputContext.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
        wsRetry = setInterval(() => {
            connectWS();
        }, RETRY_INTERVAL);
    });
}

setInterval(() => {
    if(websocketConnected){
        if(SHOW_LOGS) console.log("Sending Web Socket Request...");
        inputCanvas.toBlob((blob) =>{ws.send(blob)}, 'image/png');
    }
}, 1000 / FPS_DETECT);

async function httpRequest(){
    inputContext.drawImage(webcam, 0, 0, inputCanvas.width, inputCanvas.height);
    const data = inputCanvas.toDataURL("image/jpeg", 1.0);
    await fetch(URL="http://127.0.0.1:8000/test", {
        method : 'POST',
        body : data
    }).then((response) => {
        response.json().then((response_json) => {
            if (SHOW_LOGS) console.log(response_json);
        });
    }).catch((error) => {
        console.log(error);
    });
}