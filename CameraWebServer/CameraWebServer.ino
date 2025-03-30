#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <AsyncTCP.h>
#include "soc/soc.h"           // Disable brownout problems
#include "soc/rtc_cntl_reg.h"  // Disable brownout problems
#include "credentials.h"
#include "esp_camera.h"

#define CAMERA_MODEL_AI_THINKER // Has PSRAM
#include "camera_pins.h"

const char *ssid = SSID;
const char *password = PSW;

bool client_connected = false;

AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

// IPAddress local_IP(192, 168, 1, 184);
// IPAddress gateway(192, 168, 1, 1);
// IPAddress subnet(255, 255, 0, 0);

void startCameraServer();
void setupLedFlash(int pin);

void notifyClients(String message) {
  ws.textAll(message);
}

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len) {
  switch (type) {
    case WS_EVT_CONNECT:
      client_connected = true;
      Serial.printf("WebSocket client #%u connected from %s\n", client->id(), client->remoteIP().toString().c_str());
      break;
    case WS_EVT_DISCONNECT:
      Serial.printf("WebSocket client #%u disconnected\n", client->id());
      ws.cleanupClients();
      break;
    case WS_EVT_DATA:
      handleWebSocketMessage(arg, data, len);
      break;
    case WS_EVT_PONG:
    case WS_EVT_ERROR:
      break;
  }
}

void handleWebSocketMessage(void *arg, uint8_t *data, size_t len) {
  AwsFrameInfo *info = (AwsFrameInfo*)arg;
  if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
    data[len] = 0;
    String message = (char*)data;
    Serial.println(message);
    notifyClients(message);
  }
}

esp_err_t init_wifi() {
  // WiFi.softAP(ssid, password);
  // Serial.println(WiFi.softAPIP());
  // WiFi.mode(WIFI_STA);
  // if (!WiFi.config(local_IP, gateway, subnet)) {
  //   Serial.println("STA Failed to configure");
  // }
  WiFi.begin(ssid, password);
  Serial.println("\nCONNECTING");
  while(WiFi.status() != WL_CONNECTED){
      Serial.print(".");
      delay(100);
  }
  Serial.print("\n");
  Serial.println(WiFi.localIP());
  ws.onEvent(onEvent);
  server.addHandler(&ws);

  DefaultHeaders::Instance().addHeader("Access-Control-Allow-Origin", "*");
  DefaultHeaders::Instance().addHeader("Access-Control-Allow-Methods", "GET, POST, PUT");
  DefaultHeaders::Instance().addHeader("Access-Control-Allow-Headers", "Content-Type");

  server.on("/capture", HTTP_GET, [] (AsyncWebServerRequest *request) {
    sensor_t * s = esp_camera_sensor_get();
    s->set_framesize(s, FRAMESIZE_SVGA);
    s->set_quality(s, 20);
    camera_fb_t *fb = esp_camera_fb_get();
    delay(100);
    esp_camera_fb_return(fb);
    delay(100);
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      request->send(200, "text/plain", "Camera capture failed");
    }else{
      Serial.println("Camera Captured.");
      Serial.printf("Captured image size: %d bytes\n", fb->len);
      request->send_P(200, "image/jpeg", (const uint8_t*)fb->buf, fb->len);
    }
    esp_camera_fb_return(fb);
    s->set_framesize(s, FRAMESIZE_VGA);
    s->set_quality(s, 20);
    fb = esp_camera_fb_get();
    esp_camera_fb_return(fb);
  });

  server.begin();
  Serial.println("STARTED WEBSERVER");
  return ESP_OK;
}

esp_err_t init_camera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 10000000;
  config.pixel_format = PIXFORMAT_JPEG;

  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  //init with high specs to pre-allocate larger buffers
  if (psramFound()) {
    config.frame_size = FRAMESIZE_UXGA;
    config.jpeg_quality = 20;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
  // Camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return err;
  }
  sensor_t * s = esp_camera_sensor_get();
  s->set_framesize(s, (framesize_t) FRAMESIZE_VGA);
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
  s->set_brightness(s, 0);
  s->set_contrast(s, 1);
  Serial.println("Cam Success init");
  return ESP_OK;
};

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();
  init_camera();
  init_wifi();
}

void loop() {
  if(client_connected){
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
    }else{
      ws.binaryAll((const char*) fb->buf, fb->len);
    }
    esp_camera_fb_return(fb);
  }
  delay(400);
}
