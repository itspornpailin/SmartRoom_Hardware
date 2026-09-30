import paho.mqtt.client as mqtt
import time
import json
import random
import datetime
from typing import Dict, Any

BROKER_HOST = "localhost"
BROKER_PORT = 1883

# Hardware Nodes Definition
DOOR_NODES = ["door_left", "door_right"]
ENV_NODES = [f"env_desk_{str(i).zfill(2)}" for i in range(1, 8)]
AC_NODES = [f"ac_{str(i).zfill(2)}" for i in range(1, 8)]

def generate_timestamp() -> str:
    # Use Thailand time (UTC+7) formatted as ISO 8601
    tz_th = datetime.timezone(datetime.timedelta(hours=7))
    return datetime.datetime.now(tz_th).strftime("%Y-%m-%dT%H:%M:%S+07:00")

def generate_door_data(node_id: str) -> Dict[str, Any]:
    # Match the ESP32 payload exactly
    direction = random.choice(["IN", "OUT"])
    return {
        "node_id": node_id,
        "direction": direction,
        "current_count": random.randint(1, 50),
        "timestamp": generate_timestamp()
    }

def generate_env_data(node_id: str) -> Dict[str, Any]:
    return {
        "node_id": node_id,
        "temperature_c": round(random.uniform(22.0, 27.5), 2),
        "humidity_percent": round(random.uniform(45.0, 65.0), 2),
        "light_lux": round(random.uniform(250.0, 600.0), 2),
        "timestamp": generate_timestamp()
    }

def generate_ac_data(node_id: str) -> Dict[str, Any]:
    return {
        "node_id": node_id,
        "is_running": random.choice([True, False]),
        "timestamp": generate_timestamp()
    }

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="python_mock_generator")
    
    print(f"Connecting to MQTT Broker at {BROKER_HOST}:{BROKER_PORT}...")
    try:
        client.connect(BROKER_HOST, BROKER_PORT, 60)
    except ConnectionRefusedError:
        print("Error: Could not connect to MQTT Broker. Is Mosquitto running?")
        return

    client.loop_start()

    print("Mock Data Generator is running. Press Ctrl+C to stop.\n")
    try:
        while True:
            # 1. Simulate Door Nodes (left and right)
            for door_node in DOOR_NODES:
                if random.random() < 0.3: # 30% chance for a door event to happen
                    door_data = generate_door_data(door_node)
                    # Extract 'left' or 'right' from 'door_left' / 'door_right'
                    side = door_node.split('_')[1]
                    topic = f"greenoffice/sensor/door/{side}"
                    
                    client.publish(topic, json.dumps(door_data))
                    print(f"[PUBLISH] Door Data: {door_data['direction']} at {door_data['node_id']} (Topic: {topic})")

            # 2. Simulate Environment Nodes
            for env_node in ENV_NODES:
                env_data = generate_env_data(env_node)
                client.publish(f"greenoffice/sensor/env/{env_node}", json.dumps(env_data))
                print(f"[PUBLISH] Env Data: {env_node} (Temp: {env_data['temperature_c']}C)")

            # 3. Simulate AC Status Nodes
            for ac_node in AC_NODES:
                if random.random() < 0.2: 
                    ac_data = generate_ac_data(ac_node)
                    client.publish(f"greenoffice/sensor/ac/{ac_node}", json.dumps(ac_data))
                    print(f"[PUBLISH] AC Data: {ac_node} (Running: {ac_data['is_running']})")

            time.sleep(5)
            print("-" * 40)
            
    except KeyboardInterrupt:
        print("\nStopping generator...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    main()