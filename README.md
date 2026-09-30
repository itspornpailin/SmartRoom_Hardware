# 🌿 AIoT Green Office / Smart Room Monitoring

โปรเจกต์นี้คือระบบตรวจสอบและจัดการสภาพแวดล้อมภายในห้องทำงาน (Smart Office) โดยใช้เทคโนโลยี AIoT ซึ่งประกอบไปด้วยการอ่านค่าจากเซนเซอร์สภาพแวดล้อม (อุณหภูมิ, ความชื้น, แสง), สถานะการเปิด/ปิดแอร์, และการนับจำนวนคนเข้าออกห้องแบบเรียลไทม์

## 🧩 การทำงานของระบบ (How it works)
1. **Hardware (ESP32) / Mock Generator**: จะทำการอ่านค่าจากเซนเซอร์และส่งข้อมูล (Publish) ในรูปแบบ JSON ไปยัง **MQTT Broker**
2. **MQTT Broker (Mosquitto)**: ทำหน้าที่เป็นตัวกลางในการกระจายข้อมูล (Message Queue)
3. **Go Backend**: คอยดักฟัง (Subscribe) ข้อมูลจาก MQTT เพื่อนำไปบันทึกลงฐานข้อมูล **PostgreSQL** (พร้อมประทับตราเวลาไทย)
4. **Node-RED**: คอยดักฟังข้อมูลจาก MQTT เช่นกัน เพื่อนำมาประมวลผลและแสดงผลเป็นกราฟิกสวยงามผ่าน **Node-RED Dashboard**

---

## 🚀 ขั้นตอนการติดตั้งและเริ่มต้นใช้งาน (Installation & Setup)

### 1. ดึงโค้ดลงเครื่อง (Clone Repository)
เปิด Terminal หรือ Command Prompt แล้วรันคำสั่ง:
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. สตาร์ท Infrastructure (Database, MQTT, Node-RED)
ระบบทั้งหมดถูกรวมไว้ใน Docker Compose เพื่อให้ง่ายต่อการรัน รันคำสั่งนี้เพื่อเปิดใช้งาน:
```bash
docker-compose up -d
```
*ระบบจะเปิดใช้งาน:*
- **PostgreSQL**: Port `5432` (User: `admin`, Pass: `password`, DB: `aiot_db`)
- **Mosquitto MQTT**: Port `1883` (ไม่มีรหัสผ่าน)
- **Node-RED**: Port `1880`

### 3. เริ่มต้นระบบบันทึกฐานข้อมูล (Go Backend)
เปิด Terminal หน้าต่างใหม่ เข้าไปที่โฟลเดอร์ backend แล้วรัน:
```bash
cd backend
go mod tidy
go run main.go
```

### 4. รันตัวจำลองข้อมูล (ถ้ายังไม่มีฮาร์ดแวร์จริง)
เปิด Terminal หน้าต่างใหม่ เข้าไปที่โฟลเดอร์ mock_generator แล้วรัน:
```bash
cd mock_generator
pip install -r requirements.txt
python mock_iot.py
```

---

## ⚙️ การตั้งค่า Node-RED Dashboard (สำหรับเครื่องเพื่อนที่ดึงโค้ดไป)

ไฟล์ `flows.json` ใน Repository นี้ประกอบด้วยหน้า Dashboard และ Subflow ทั้งหมดแล้ว

1. **เข้าสู่ระบบ Node-RED**: เปิดเบราว์เซอร์ไปที่ `http://localhost:1880`
2. **Import โค้ด**: ไปที่เมนูมุมขวาบน (ขีด 3 ขีด) > เลือก `Import` > เลือก `select a file to import` แล้วอัปโหลดไฟล์ `flows.json` จากโปรเจกต์
3. **ติดตั้ง Node ที่จำเป็น**: หากมีแจ้งเตือนว่าขาด Node (เช่น Dashboard) ให้ไปที่เมนู `Manage palette` > แท็บ `Install` แล้วค้นหา `node-red-dashboard` กดติดตั้งให้เรียบร้อย
4. **การตั้งค่ารหัสผ่าน MQTT (สำคัญ)**: 
   เนื่องจากไฟล์รหัสผ่าน (`flows_cred.json`) ถูกยกเว้นการอัปโหลดขึ้น Git เพื่อความปลอดภัย ทำให้คุณต้องเชื่อมต่อ MQTT ใหม่ 
   - ให้ดับเบิลคลิกที่โหนด `mqtt in` ตัวใดตัวหนึ่ง 
   - กดที่ไอคอนรูปดินสอหลังชื่อ Server
   - หากรันผ่าน Docker ที่เตรียมไว้ ให้ชี้ Server ไปที่ `mqtt-broker` (หรือ `localhost`) Port `1883` โดย**ไม่ต้องใส่รหัสผ่าน**
   - *(แต่ถ้าโปรเจกต์ของคุณเชื่อมต่อกับ Cloud MQTT ภายนอก ให้ไปที่แท็บ Security แล้วกรอก Username / Password ให้ถูกต้อง)*

---

## 📡 โครงสร้าง MQTT Topics & Message Payloads

ระบบใช้การส่งข้อมูลผ่าน MQTT เป็นรูปแบบ JSON Object แบ่งออกเป็น 3 ส่วนหลัก ดังนี้:

### 1. เซนเซอร์สภาพแวดล้อม (Environment Sensors)
ครอบคลุมข้อมูลอุณ পণ্ডিত ความชื้น และความสว่างของโต๊ะทำงาน (มีทั้งหมด 7 โต๊ะ)
- **Topic (เจาะจง)**: `greenoffice/sensor/env/env_desk_01` (ไล่ไปจนถึง 07)
- **Topic (รับทั้งหมด)**: `greenoffice/sensor/env/+`
- **Message Payload**:
```json
{
  "node_id": "env_desk_01",
  "temperature_c": 24.52,
  "humidity_percent": 55.40,
  "light_lux": 420.15,
  "timestamp": "2026-09-30T19:54:00+07:00"
}
```
- **ตัวแปรที่ใช้ใน Node-RED**: `msg.payload.temperature_c`, `msg.payload.light_lux`

### 2. สถานะเครื่องปรับอากาศ (AC Status)
ครอบคลุมสถานะการเปิด/ปิด ของแอร์ (มีทั้งหมด 7 ตัว)
- **Topic (เจาะจง)**: `greenoffice/sensor/ac/ac_01` (ไล่ไปจนถึง 07)
- **Topic (รับทั้งหมด)**: `greenoffice/sensor/ac/+`
- **Message Payload**:
```json
{
  "node_id": "ac_01",
  "is_running": true,
  "timestamp": "2026-09-30T19:54:00+07:00"
}
```
- **ตัวแปรที่ใช้ใน Node-RED**: `msg.payload.is_running`

### 3. เซนเซอร์คนเข้า-ออกประตู (Door Sensor - แยกซ้าย/ขวา)
นับจำนวนคนเข้าออกและสรุปยอดคนในห้องแบบเรียลไทม์จากประตูฝั่งซ้ายและฝั่งขวา
- **Topic (ประตูซ้าย)**: `greenoffice/sensor/door/left`
- **Topic (ประตูขวา)**: `greenoffice/sensor/door/right`
- **Topic (รับทั้งหมด)**: `greenoffice/sensor/door/+`
- **Message Payload**:
```json
{
  "node_id": "door_left",
  "direction": "IN", 
  "current_count": 15,
  "timestamp": "2026-09-30T19:54:00+07:00"
}
```
- **ตัวแปรที่ใช้ใน Node-RED**: `msg.payload.direction`, `msg.payload.current_count`

---

## 🛠 ข้อมูลเกี่ยวกับ Subflow (แม่พิมพ์อัจฉริยะ)
ในหน้าหลัก (Flow 1) จะใช้ระบบ Subflow เพื่อลดความซ้ำซ้อนของโค้ด:
- **ENV Subflow**: ใช้ตัวแปรแวดล้อม `DESK_ID` เป็นตัวกรอง (เช่น ตั้งค่าเป็น `env_desk_01`)
- **AC Subflow**: ใช้ตัวแปรแวดล้อม `AC_ID` เป็นตัวกรอง (เช่น ตั้งค่าเป็น `ac_01`)

**วิธีเพิ่มโหนดใหม่**: หากมีการเพิ่มโต๊ะทำงานหรือแอร์ในอนาคต เพียงแค่ Copy กล่อง Subflow ที่มีอยู่แล้ววางใหม่ จากนั้นดับเบิลคลิกที่กล่องเพื่อเข้าไปเปลี่ยนค่า ID ในหมวด Properties (Environment Variables) ก็พร้อมใช้งานทันที ไม่ต้องเดินสายโหนดใหม่!
