/*
 * AIoT Green Office - Environment Node (SHT30 + BH1750)
 * Node ID: env_desk_06
 * Topic: greenoffice/sensor/env/desk_06
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_SHT31.h>
#include <BH1750.h>
#include "config_template.h"

const char* NODE_ID = "env_desk_06";
const char* MQTT_TOPIC = "greenoffice/sensor/env/desk_06";

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
      payload += "\"node_id\":\"" + String(NODE_ID) + "\",";
      payload += "\"temperature_c\":" + String(t, 2) + ",";
      payload += "\"humidity_percent\":" + String(h, 2) + ",";
      payload += "\"light_lux\":" + String(lux, 2);
      payload += "}";

      Serial.print("Publishing: ");
      Serial.println(payload);
      mqttClient.publish(MQTT_TOPIC, payload.c_str());
    } else {
      Serial.println("Sensor error");
    }
  }
}
