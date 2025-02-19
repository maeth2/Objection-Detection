document.body.onload = function(){init()}
var canvas, ctx;
var showLogs = false

function init(){
    console.log("INITIALIZING");
    canvas = document.getElementById("output");
    ctx = canvas.getContext("2d");
}

const webcam = document.getElementById("videoElement");
const contraints = {
    video : {
        facingMode : 'enviroment'
    }
}
navigator.mediaDevices.getUserMedia(contraints).then((stream) => {
    webcam.srcObject = stream;
    webcam.play();
}).catch((error) =>{
    console.error(error);
});
webcam.addEventListener('click', httpRequest)

var ws = new WebSocket("ws://127.0.0.1:8000/detect")
ws.addEventListener('message', function (event){
    if (showLogs){
        console.log("Receiving Web Socket Message ->")
        console.log(event.data);
    }
});

setInterval(wsRequest, 1000);
async function wsRequest(){
    if(showLogs) console.log("Sending Web Socket Request...")
    ctx.drawImage(webcam, 0, 0, canvas.width, canvas.height);
    console.log(webcam.width, webcam.height, canvas.width, canvas.height)
    canvas.toBlob((blob) =>{ws.send(blob)}, 'image/png');
    ctx.drawImage(webcam, 0, 0, canvas.width, canvas.height);
}

async function httpRequest(){
    ctx.drawImage(webcam, 0, 0, canvas.width, canvas.height)
    const data = canvas.toDataURL("image/jpeg", 1.0)
    await fetch(URL="http://127.0.0.1:8000/test", {
        method : 'POST',
        body : data
    }).then((response) => {
        response.json().then((response_json) => {
            if (showLogs) console.log(response_json)
        })
        // response.json().then((response_json) => response_json.forEach(box => {
        //     console.log(box)
        // }))
    }).catch((error) => {
        console.log(error)
    });
}