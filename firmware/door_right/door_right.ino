/*
 * AIoT Green Office - Door Status Node (VL53L5CX ToF Sensor)
 * Node ID: door_right (ประตูบานที่ 2)
 * Topic: greenoffice/sensor/door/right
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <SparkFun_VL53L5CX_Library.h>
#include "config_template.h"

const char* NODE_ID = "door_right";
const char* MQTT_TOPIC = "greenoffice/sensor/door/right";

WiFiClient espClient;
PubSubClient mqttClient(espClient);
SparkFun_VL53L5CX myImager;
VL53L5CX_ResultsData measurementData; 

int currentOccupancy = 0;

// ==========================================
// 🚶 Rule-Based State Machine Variables
// ==========================================
bool activeZoneA = false;
bool activeZoneB = false;
unsigned long lastActivityTime = 0;
const unsigned long TIMEOUT_MS = 1500; // Reset state ถ้าคนเดินไม่สุดใน 1.5 วินาที

// ระยะความสูงที่เซนเซอร์จะมองว่าเป็น "คน" (สมมติว่าเซนเซอร์ติดเพดานสูง 2 เมตร)
// ถ้าระยะต่ำกว่า 1800 mm หมายถึงมีคนเดินผ่าน
const int DISTANCE_THRESHOLD = 1800; 

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
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  
  Serial.println("Initializing VL53L5CX...");
  if (myImager.begin() == false) {
    Serial.println(F("Sensor not found - check your wiring. Freezing..."));
    while (1);
  }
  
  myImager.setResolution(8 * 8); // เซ็ตเป็น 8x8 zones (รวม 64 โซน)
  myImager.startRanging();

  setup_wifi();
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
}

void publishEvent(String direction) {
  String payload = "{";
  payload += "\"node_id\":\"" + String(NODE_ID) + "\",";
  payload += "\"direction\":\"" + direction + "\",";
  payload += "\"current_count\":" + String(currentOccupancy);
  payload += "}";

  Serial.print("Publishing: ");
  Serial.println(payload);
  mqttClient.publish(MQTT_TOPIC, payload.c_str());
}

void detectDirection(VL53L5CX_ResultsData *data) {
  bool currentZoneA = false;
  bool currentZoneB = false;

  // อ่านค่าจาก 64 โซน โดยแบ่ง 32 โซนแรกเป็น Zone A, 32 โซนหลังเป็น Zone B
  for (int i = 0; i < 64; i++) {
    // 5 = Range Valid, 9 = Range Valid with large pulse
    if (data->target_status[VL53L5CX_TARGET_PER_ZONE * i] == 5 || 
        data->target_status[VL53L5CX_TARGET_PER_ZONE * i] == 9) {
          
      if (data->distance_mm[VL53L5CX_TARGET_PER_ZONE * i] < DISTANCE_THRESHOLD) {
        if (i < 32) {
          currentZoneA = true;
        } else {
          currentZoneB = true;
        }
      }
    }
  }

  // --- Timeout Check ---
  // ถ้ายืนค้างนานเกิน TIMEOUT ให้ยกเลิก State 
  if ((activeZoneA || activeZoneB) && (millis() - lastActivityTime > TIMEOUT_MS)) {
    activeZoneA = false;
    activeZoneB = false;
  }

  // --- State Machine ---
  if (!activeZoneA && !activeZoneB) {
    // ยังไม่มีคน รอการตัดผ่าน
    if (currentZoneA && !currentZoneB) {
      activeZoneA = true;
      lastActivityTime = millis();
    } else if (currentZoneB && !currentZoneA) {
      activeZoneB = true;
      lastActivityTime = millis();
    }
  } else if (activeZoneA && !activeZoneB) {
    // คนเข้ามาจากฝั่ง A แล้ว (รอตัดผ่าน B)
    if (currentZoneB) {
      currentOccupancy++; // IN
      publishEvent("IN");
      activeZoneA = false;
      activeZoneB = false; // Reset State
      delay(500); // หน่วงเวลาป้องกันเงาซ้อน
    }
  } else if (activeZoneB && !activeZoneA) {
    // คนเข้ามาจากฝั่ง B แล้ว (รอตัดผ่าน A)
    if (currentZoneA) {
      currentOccupancy--; // OUT
      if (currentOccupancy < 0) currentOccupancy = 0;
      publishEvent("OUT");
      activeZoneA = false;
      activeZoneB = false; // Reset State
      delay(500); // หน่วงเวลาป้องกันเงาซ้อน
    }
  }
}

void loop() {
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop();

  if (myImager.isDataReady() == true) {
    if (myImager.getRangingData(&measurementData)) {
      detectDirection(&measurementData);
    }
  }
}
