#ifndef CONFIG_TEMPLATE_H
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
