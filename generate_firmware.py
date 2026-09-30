import os
import shutil

BASE_DIR = r"G:\CMU\Project\Hardware_Simulate\firmware"

CONFIG_TEMPLATE = """#ifndef CONFIG_TEMPLATE_H
#define CONFIG_TEMPLATE_H

// ==========================================
// 🔧 AIoT Green Office - Configuration File
// ==========================================

// --- 📶 Wi-Fi Configuration ---
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// --- 🌐 MQTT Configuration ---
const char* MQTT_SERVER = "192.168.1.100"; // เปลี่ยนเป็น IP ของ MQTT Broker (Mosquitto)
const int MQTT_PORT = 1883;
const char* MQTT_USER = "";     // ใส่หาก MQTT มี Username
const char* MQTT_PASSWORD = ""; // ใส่หาก MQTT มี Password

// --- 🔌 Pinout Configuration ---
// [Environment Node] SHT30 & BH1750 (I2C)
const int I2C_SDA_PIN = 21; // ต่อสาย SDA ของเซนเซอร์เข้าขา 21
const int I2C_SCL_PIN = 22; // ต่อสาย SCL ของเซนเซอร์เข้าขา 22

// [AC Status Node] Vibration Sensor (SW-420)
const int VIBRATION_PIN = 34; // อ่านค่าแอนะล็อกจากการสั่นของแอร์

// --- ⏱️ Timing Settings ---
const unsigned long PUBLISH_INTERVAL_MS = 120000; // ส่งข้อมูลทุกๆ 2 นาที (120,000 ms)

#endif // CONFIG_TEMPLATE_H
"""

ENV_INO_TEMPLATE = """/*
 * AIoT Green Office - Environment Node (SHT30 + BH1750)
 * Node ID: {NODE_ID}
 * Topic: greenoffice/sensor/env/{NODE_NAME}
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_SHT31.h>
#include <BH1750.h>
#include "config_template.h"

const char* NODE_ID = "{NODE_ID}";
const char* MQTT_TOPIC = "greenoffice/sensor/env/{NODE_NAME}";

WiFiClient espClient;
PubSubClient mqttClient(espClient);
Adafruit_SHT31 sht31 = Adafruit_SHT31();
BH1750 lightMeter;

unsigned long lastMsgTime = 0;

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

  if (!sht31.begin(0x44)) {
    Serial.println("SHT31 not found. Please check wiring!");
  }

  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println(F("BH1750 initialized"));
  } else {
    Serial.println(F("Error initializing BH1750"));
  }

  setup_wifi();
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
}

void loop() {
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastMsgTime > PUBLISH_INTERVAL_MS) {
    lastMsgTime = now;

    float t = sht31.readTemperature();
    float h = sht31.readHumidity();
    float lux = lightMeter.readLightLevel();

    if (!isnan(t)) {
      String payload = "{";
      payload += "\\"node_id\\":\\"" + String(NODE_ID) + "\\",";
      payload += "\\"temperature_c\\":" + String(t, 2) + ",";
      payload += "\\"humidity_percent\\":" + String(h, 2) + ",";
      payload += "\\"light_lux\\":" + String(lux, 2);
      payload += "}";

      Serial.print("Publishing: ");
      Serial.println(payload);
      mqttClient.publish(MQTT_TOPIC, payload.c_str());
    } else {
      Serial.println("Sensor error");
    }
  }
}
"""

AC_INO_TEMPLATE = """/*
 * AIoT Green Office - AC Status Node (Vibration Sensor)
 * Node ID: {NODE_ID}
 * Topic: greenoffice/sensor/ac/{NODE_NAME}
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include "config_template.h"

const char* NODE_ID = "{NODE_ID}";
const char* MQTT_TOPIC = "greenoffice/sensor/ac/{NODE_NAME}";

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
    payload += "\\"node_id\\":\\"" + String(NODE_ID) + "\\",";
    payload += "\\"is_running\\":" + String(isRunning ? "true" : "false") + ",";
    payload += "\\"vibration_raw\\":" + String(avgVibration);
    payload += "}";

    Serial.print("Publishing: ");
    Serial.println(payload);
    mqttClient.publish(MQTT_TOPIC, payload.c_str());
  }
}
"""

def make_firmware_folders():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    # 1. เขียนไฟล์ config_template.h ไว้ที่ Root ของ firmware/ เผื่ออ้างอิง
    with open(os.path.join(BASE_DIR, "config_template.h"), "w", encoding="utf-8") as f:
        f.write(CONFIG_TEMPLATE)

    # 2. สร้าง Env Nodes
    for i in range(1, 8):
        node_id = f"env_desk_{i:02d}"
        node_name = f"desk_{i:02d}"
        folder_path = os.path.join(BASE_DIR, node_id)
        os.makedirs(folder_path, exist_ok=True)
        
        # เขียน .ino
        with open(os.path.join(folder_path, f"{node_id}.ino"), "w", encoding="utf-8") as f:
            f.write(ENV_INO_TEMPLATE.replace("{NODE_ID}", node_id).replace("{NODE_NAME}", node_name))
        
        # ก๊อปปี้ config เข้าไปในโฟลเดอร์เพื่อให้ Arduino IDE ค้นหาเจอ
        with open(os.path.join(folder_path, "config_template.h"), "w", encoding="utf-8") as f:
            f.write(CONFIG_TEMPLATE)

    # 3. สร้าง AC Nodes
    for i in range(1, 8):
        node_id = f"ac_unit_{i:02d}"
        node_name = f"unit_{i:02d}"
        folder_path = os.path.join(BASE_DIR, node_id)
        os.makedirs(folder_path, exist_ok=True)
        
        # เขียน .ino
        with open(os.path.join(folder_path, f"{node_id}.ino"), "w", encoding="utf-8") as f:
            f.write(AC_INO_TEMPLATE.replace("{NODE_ID}", node_id).replace("{NODE_NAME}", node_name))
            
        # ก๊อปปี้ config เข้าไปในโฟลเดอร์เพื่อให้ Arduino IDE ค้นหาเจอ
        with open(os.path.join(folder_path, "config_template.h"), "w", encoding="utf-8") as f:
            f.write(CONFIG_TEMPLATE)
            
    print("Firmware structure generated successfully.")

if __name__ == "__main__":
    make_firmware_folders()
