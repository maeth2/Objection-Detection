document.body.onload = function(){init()}

const DEBUG = false;
const DETECTION_ADDRESS = '8000';
const CAMERA_ADDRESS = 'http://172.20.10.9:80'
const RETRY_INTERVAL = 1000;
const LABEL_RESOLUTION = 2;
const FPS = 60, FPS_DETECT = 3;

var externalWebCam = true;
var internalWebCam = false;
var addresses = {}

var inputCanvas, inputContext, outputCanvas, outputContext, labelCanvas, labelContext;
var wsDetect, wsDetectRetry, wsCamera, wsCameraRetry;
var onMobileDevice = false;
var detectWebsocketConnected = false;
var webCamDirection = 'user';
var outputText;
var storedURL;
var utterance;

async function getURL(){
    await fetch('tunnels.json').then(response => {
        response.json().then(response_json => {
            response_json['tunnels'].forEach(tunnel => {
                var url = tunnel['public_url'].replace('https://', '');
                var port = tunnel['config']['addr'].replace("http://localhost:", '');
                addresses[port] = url;
            })
        });
    })
    console.log(addresses)
}

async function init(){
    console.log("INITIALIZING");
    await getURL();
    inputCanvas = document.getElementById("input");
    inputContext = inputCanvas.getContext("2d");
    outputCanvas = document.getElementById("output");
    outputContext = outputCanvas.getContext("2d");
    labelCanvas = document.getElementById("labels");
    labelContext = labelCanvas.getContext("2d");
    labelCanvas.width = labelCanvas.width * LABEL_RESOLUTION;
    labelCanvas.height = labelCanvas.height * LABEL_RESOLUTION;
    outputText = document.getElementById("detect");
    utterance = new SpeechSynthesisUtterance();
    utterance.text = "NOTHING DETECTED";
    checkMobileDevice();
    connectDetectionWS();
    connectCameraWS();
}

function checkMobileDevice(){
    onMobileDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    if(onMobileDevice){
        document.getElementsByClassName("output-container")[0].style.display = 'none';
        document.getElementsByClassName("video-button-container")[0].style.width = '90%'
        document.getElementsByClassName("video-button-container")[0].style.height = '70%'
        document.getElementById('flip').style.display = 'block'
    }
}

const webcam = document.createElement('video');
startWebCam(webcam)

function startWebCam(webcam){
    console.log("internalWebCam STARTED");
    const contraints = {
        video : {
            facingMode: webCamDirection
        },
        audio : false
    }
    navigator.mediaDevices.getUserMedia(contraints).then((stream) => {
        if('srcObject' in webcam) {
            webcam.srcObject = stream;
        }else{
            webcam.src = window.createObjectURL(stream);
        }
        webcam.setAttribute('autoplay', '');
        webcam.setAttribute('muted', '');
        webcam.setAttribute('playsinline', '');
        webcam.play();
        setInterval(() =>{
            if(!externalWebCam || internalWebCam){
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

function flipWebCam(webcam){
    webCamDirection = webCamDirection == 'user' ? 'enviroment' : 'user';
    startWebCam(webcam);
}

function connectDetectionWS(){
    var address = "wss://" + addresses[DETECTION_ADDRESS] + "/detect";
    console.log("ATTEMPTING CONNECTION TO: ", address);
    wsDetect = new WebSocket(address);
    clearInterval(wsDetectRetry);
    wsDetect.addEventListener('message', (event) => {
        outputContext.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
        labelContext.clearRect(0, 0, labelCanvas.width, labelCanvas.height);
        var boxes = JSON.parse(event.data);
        if(DEBUG) console.table(boxes);
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
        detectWebsocketConnected = true;
        console.log("CONNECTED TO: ", address);
    });
    wsDetect.addEventListener('close', (event) => {
        console.log("DISCONNECTED FROM: ", address);
        detectWebsocketConnected = false;
        outputContext.clearRect(0, 0, outputCanvas.width, outputCanvas.height);
        clearInterval(wsDetectRetry);
        wsDetectRetry = setInterval(() => {
            console.log("RETRYING CONNECTION TO: ", address);
            connectDetectionWS();
        }, RETRY_INTERVAL);
    });
}

function setCameraTimeout(time){
    var timeout = setTimeout(() => {
        console.log("TIMED OUT. REVERTING BACK TO BUILT IN CAMERA.")
        externalWebCam = false;
    }, time);
    return timeout;
}

function connectCameraWS(){
    var address = "wss://" + addresses[CAMERA_ADDRESS] + "/ws";
    console.log("ATTEMPTING CONNECTION TO: ", address);
    wsCamera = new WebSocket(address);
    console.log("SUCESSFULLY CONNECTED TO: ", address);
    clearInterval(wsCameraRetry);

    var timeout = setCameraTimeout(2000);

    wsCamera.addEventListener('message', (event) => {
        clearInterval(timeout);
        timeout = setCameraTimeout(2000);
        externalWebCam = true;
        if (externalWebCam && !internalWebCam){
            URL.revokeObjectURL(storedURL);
            var img = new Image();
            img.onload = function() {
                inputContext.clearRect(0, 0, inputCanvas.width, inputCanvas.height);
                inputContext.drawImage(img, 0, 0, inputCanvas.width, inputCanvas.height)
            }
            img.src = URL.createObjectURL(event.data);
            storedURL = img.src;
        }
    });
    wsCamera.addEventListener('open', (event) => {
        console.log("CONNECTED TO: ", address);
    });
    wsCamera.addEventListener('close', (event) => {
        console.log("DISCONNECTED FROM: ", address);
        clearInterval(wsCameraRetry);
        wsCameraRetry = setInterval(() => {
            console.log("RETRYING CONNECTION TO: ", address);
            connectCameraWS();
        }, RETRY_INTERVAL);
    });
}

async function httpImgToText(){
    // if(!internalWebCam){
    //     console.log("FETCHING CAMERA IMAGE");
    //     const response = await fetch(CAMERA_WEBSERVER_CAPTURE_ADDRESS, {
    //         method : 'GET'
    //     })
    //     const blob = await response.blob();
    //     var img = new Image();
    //     img.onload = function() {
    //         testContext.clearRect(0, 0, testCanvas.width, testCanvas.height);
    //         testContext.drawImage(img, 0, 0, testCanvas.width, testCanvas.height)
    //     }
    //     img.src = URL.createObjectURL(blob);
    // }
    
    const data = inputCanvas.toDataURL("image/jpeg", 1.0);
    await fetch("https://" + addresses[DETECTION_ADDRESS] + "/detect_text", {
        method : 'POST',
        body : data
    }).then((response) => {
        response.json().then((response_json) => {
            var output = "";
            var text = ""
            console.log(response_json['text']);
            response_json['detect'].forEach(element => {
                output += element["label"] + "<br>";
                text += element["label"] + "!";
            })
            outputText.innerHTML = output;
            speak(text);
        });
    }).catch((error) => {
        console.log(error);
    });
}

async function speak(text){
    if(text != null){
        utterance.text = text;
    }
    speechSynthesis.speak(utterance);
}

//UPDATE DISPLAY EACH FRAME
setInterval(() => {
    if(detectWebsocketConnected){
        if(DEBUG) console.log("Sending Web Socket Request...");
        inputCanvas.toBlob((blob) =>{wsDetect.send(blob)}, 'image/png');
    }
}, 1000 / FPS_DETECT);

//TURNING OFF AND ON WEBCAM
Array.from(document.getElementsByClassName("video")).forEach((button) => button.addEventListener('click', () => {
    document.getElementById("video_on").style.display = !internalWebCam ? 'block' : 'none';
    document.getElementById("video_off").style.display = internalWebCam ? 'block' : 'none';
    internalWebCam = !internalWebCam;
}));

document.getElementById("camera").addEventListener('click', httpImgToText);
document.getElementById("sound").addEventListener('click', ()=>{speak(null)});
document.getElementById("flip").addEventListener('click', ()=>{flipWebCam(webcam)});