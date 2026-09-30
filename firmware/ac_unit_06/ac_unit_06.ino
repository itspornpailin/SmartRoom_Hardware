/*
 * AIoT Green Office - AC Status Node (Vibration Sensor)
 * Node ID: ac_unit_06
 * Topic: greenoffice/sensor/ac/unit_06
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include "config_template.h"

const char* NODE_ID = "ac_unit_06";
const char* MQTT_TOPIC = "greenoffice/sensor/ac/unit_06";

WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long lastMsgTime = 0;
bool lastAcState = false;
int vibrationSum = 0;
int readCount = 0;
const int VIBRATION_THRESHOLD = 500; // ปรับค่า Threshold ตามเซนเซอร์จริง (0-4095)

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("WiFi connected - IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (mqttClient.connect(NODE_ID, MQTT_USER, MQTT_PASSWORD)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(VIBRATION_PIN, INPUT);
  setup_wifi();
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
}

void loop() {
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop();

  // อ่านค่าแอนะล็อกสะสมเพื่อหาค่าเฉลี่ย
  int currentVibration = analogRead(VIBRATION_PIN);
  vibrationSum += currentVibration;
  readCount++;

  unsigned long now = millis();
  if (now - lastMsgTime > PUBLISH_INTERVAL_MS) {
    lastMsgTime = now;
    
    int avgVibration = vibrationSum / readCount;
    bool isRunning = avgVibration > VIBRATION_THRESHOLD;
    
    vibrationSum = 0;
    readCount = 0;

    String payload = "{";
    payload += "\"node_id\":\"" + String(NODE_ID) + "\",";
    payload += "\"is_running\":" + String(isRunning ? "true" : "false") + ",";
    payload += "\"vibration_raw\":" + String(avgVibration);
    payload += "}";

    Serial.print("Publishing: ");
    Serial.println(payload);
    mqttClient.publish(MQTT_TOPIC, payload.c_str());
  }
}
