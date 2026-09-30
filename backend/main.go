package main

import (
	"database/sql"
	"encoding/json"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
	_ "github.com/lib/pq"
)

// Structs for JSON Payloads
type DoorPayload struct {
	NodeID         string    `json:"node_id"`
	EventType      string    `json:"event_type"`    // From Mock
	Direction      string    `json:"direction"`     // From ESP32
	CountChange    int       `json:"count_change"`  // From Mock
	CurrentCount   int       `json:"current_count"` // From ESP32
	TotalOccupancy int       `json:"total_occupancy"`// From Mock
	Timestamp      time.Time `json:"timestamp"`
}

type EnvPayload struct {
	NodeID          string    `json:"node_id"`
	TemperatureC    float64   `json:"temperature_c"`
	HumidityPercent float64   `json:"humidity_percent"`
	LightLux        float64   `json:"light_lux"`
	Timestamp       time.Time `json:"timestamp"`
}

type ACPayload struct {
	NodeID    string    `json:"node_id"`
	IsRunning bool      `json:"is_running"`
	Timestamp time.Time `json:"timestamp"`
}

var db *sql.DB
var thaiTime *time.Location

func init() {
	var err error
	thaiTime, err = time.LoadLocation("Asia/Bangkok")
	if err != nil {
		log.Println("Timezone data not found, falling back to manual offset UTC+7")
		thaiTime = time.FixedZone("ICT", 7*3600)
	}
}

func main() {
	log.Println("Starting AIoT Backend...")

	// 1. Connect to PostgreSQL
	connStr := "postgres://admin:password@localhost:5432/aiot_db?sslmode=disable"
	var err error
	
	for i := 0; i < 5; i++ {
		db, err = sql.Open("postgres", connStr)
		if err == nil {
			err = db.Ping()
			if err == nil {
				break
			}
		}
		log.Printf("Waiting for DB connection... (%d/5)\n", i+1)
		time.Sleep(2 * time.Second)
	}

	if err != nil {
		log.Fatal("Failed to connect to PostgreSQL:", err)
	}
	defer db.Close()
	log.Println("Connected to PostgreSQL successfully")

	// 2. Connect to MQTT Broker
	opts := mqtt.NewClientOptions()
	opts.AddBroker("tcp://localhost:1883")
	opts.SetClientID("go_backend_subscriber")
	opts.SetOnConnectHandler(func(client mqtt.Client) {
		log.Println("Connected to MQTT Broker successfully")
		
		// Subscribe to topics
		subscribe(client, "greenoffice/sensor/door/+", messagePubHandler)
		subscribe(client, "greenoffice/sensor/door", messagePubHandler) // For mock backward compatibility
		subscribe(client, "greenoffice/sensor/env/+", messagePubHandler)
		subscribe(client, "greenoffice/sensor/ac/+", messagePubHandler)
	})
	opts.SetConnectionLostHandler(func(client mqtt.Client, err error) {
		log.Printf("MQTT connection lost: %v", err)
	})

	client := mqtt.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		log.Fatal("Failed to connect to MQTT Broker:", token.Error())
	}

	// Keep the application running gracefully
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan
	
	log.Println("Shutting down backend...")
	client.Disconnect(250)
}

func subscribe(client mqtt.Client, topic string, handler mqtt.MessageHandler) {
	token := client.Subscribe(topic, 1, handler)
	token.Wait()
	if token.Error() != nil {
		log.Printf("Error subscribing to %s: %v", topic, token.Error())
	} else {
		log.Printf("Subscribed to topic: %s", topic)
	}
}

var messagePubHandler mqtt.MessageHandler = func(client mqtt.Client, msg mqtt.Message) {
	topic := msg.Topic()
	payload := msg.Payload()

	if strings.HasPrefix(topic, "greenoffice/sensor/door") {
		var data DoorPayload
		if err := json.Unmarshal(payload, &data); err != nil {
			log.Printf("Error parsing DoorPayload: %v", err)
			return
		}
		
		// Map ESP32 format to DB format
		eventType := data.EventType
		if eventType == "" {
			eventType = data.Direction
		}
		
		totalOccupancy := data.TotalOccupancy
		if data.CurrentCount != 0 || data.TotalOccupancy == 0 {
			totalOccupancy = data.CurrentCount
		}

		countChange := data.CountChange
		if countChange == 0 {
			countChange = 1 // Default
		}

		// Insert Thailand Timestamp if missing from hardware
		if data.Timestamp.IsZero() {
			data.Timestamp = time.Now().In(thaiTime)
		}
		
		_, err := db.Exec(`
			INSERT INTO door_logs (node_id, event_type, count_change, total_occupancy, recorded_at)
			VALUES ($1, $2, $3, $4, $5)`,
			data.NodeID, eventType, countChange, totalOccupancy, data.Timestamp)
			
		if err != nil {
			log.Printf("Error inserting DoorPayload: %v", err)
		} else {
			log.Printf("[DB] Inserted Door Data for %s at %s", data.NodeID, data.Timestamp.Format(time.RFC3339))
		}

	} else if strings.HasPrefix(topic, "greenoffice/sensor/env/") {
		var data EnvPayload
		if err := json.Unmarshal(payload, &data); err != nil {
			log.Printf("Error parsing EnvPayload: %v", err)
			return
		}
		
		if data.Timestamp.IsZero() {
			data.Timestamp = time.Now().In(thaiTime)
		}
		
		_, err := db.Exec(`
			INSERT INTO environment_logs (node_id, temperature_c, humidity_percent, light_lux, recorded_at)
			VALUES ($1, $2, $3, $4, $5)`,
			data.NodeID, data.TemperatureC, data.HumidityPercent, data.LightLux, data.Timestamp)
			
		if err != nil {
			log.Printf("Error inserting EnvPayload: %v", err)
		} else {
			log.Printf("[DB] Inserted Environment Data for %s at %s", data.NodeID, data.Timestamp.Format(time.RFC3339))
		}

	} else if strings.HasPrefix(topic, "greenoffice/sensor/ac/") {
		var data ACPayload
		if err := json.Unmarshal(payload, &data); err != nil {
			log.Printf("Error parsing ACPayload: %v", err)
			return
		}
		
		if data.Timestamp.IsZero() {
			data.Timestamp = time.Now().In(thaiTime)
		}
		
		_, err := db.Exec(`
			INSERT INTO ac_status_logs (node_id, is_running, recorded_at)
			VALUES ($1, $2, $3)`,
			data.NodeID, data.IsRunning, data.Timestamp)
			
		if err != nil {
			log.Printf("Error inserting ACPayload: %v", err)
		} else {
			log.Printf("[DB] Inserted AC Data for %s at %s", data.NodeID, data.Timestamp.Format(time.RFC3339))
		}
	} else {
		log.Printf("Received message on unhandled topic %s", topic)
	}
}
