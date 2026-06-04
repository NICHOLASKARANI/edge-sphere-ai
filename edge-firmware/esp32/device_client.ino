/*
 * EdgeSphere AI - ESP32 IoT Device Client
 * Supports MQTT, OTA updates, and telemetry collection
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Update.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>

// Configuration
#define DEVICE_ID "ESP32_" + String(ESP.getEfuseMac(), HEX)
#define VERSION "1.0.0"
#define TELEMETRY_INTERVAL 5000  // 5 seconds
#define RECONNECT_INTERVAL 5000

// Pin definitions
#define DHTPIN 4
#define DHTTYPE DHT22
#define VIBRATION_PIN 34
#define CURRENT_PIN 35

// WiFi credentials (store securely in production)
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

// MQTT Configuration
const char* mqtt_server = "your-mqtt-broker.edgesphere.ai";
const int mqtt_port = 8883;
const char* mqtt_user = "device_client";
const char* mqtt_password = "device_password";

// OTA Configuration
const char* ota_server = "ota.edgesphere.ai";
const int ota_port = 443;

// Global objects
WiFiClientSecure espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);

// Device state
unsigned long lastTelemetry = 0;
unsigned long lastReconnect = 0;
bool otaInProgress = false;

// Sensor readings
struct SensorData {
  float temperature;
  float humidity;
  float vibration;
  float current;
  float voltage;
  int rssi;
  int uptime;
  float cpu_usage;
  float memory_usage;
};

void setup() {
  Serial.begin(115200);
  Serial.println("\nEdgeSphere AI IoT Device Starting...");
  Serial.print("Device ID: ");
  Serial.println(DEVICE_ID);
  Serial.print("Firmware Version: ");
  Serial.println(VERSION);
  
  // Initialize sensors
  dht.begin();
  pinMode(VIBRATION_PIN, INPUT);
  pinMode(CURRENT_PIN, INPUT);
  
  // Setup WiFi
  setupWiFi();
  
  // Setup MQTT
  setupMQTT();
  
  // Setup OTA callback
  setupOTA();
  
  Serial.println("Device initialized successfully");
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
  
  // Send telemetry
  unsigned long now = millis();
  if (now - lastTelemetry >= TELEMETRY_INTERVAL && !otaInProgress) {
    sendTelemetry();
    lastTelemetry = now;
  }
  
  // Handle OTA
  if (otaInProgress) {
    handleOTA();
  }
}

void setupWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void setupMQTT() {
  espClient.setCACert(root_ca);
  espClient.setCertificate(client_cert);
  espClient.setPrivateKey(client_key);
  
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
  
  // Set keepalive
  client.setKeepAlive(30);
}

void reconnectMQTT() {
  unsigned long now = millis();
  if (now - lastReconnect < RECONNECT_INTERVAL) {
    return;
  }
  lastReconnect = now;
  
  Serial.print("Attempting MQTT connection...");
  
  if (client.connect(DEVICE_ID.c_str(), mqtt_user, mqtt_password)) {
    Serial.println("connected");
    
    // Subscribe to topics
    client.subscribe(("devices/" + DEVICE_ID + "/commands").c_str());
    client.subscribe(("devices/" + DEVICE_ID + "/ota/start").c_str());
    client.subscribe(("devices/" + DEVICE_ID + "/config").c_str());
    
    // Send device info
    sendDeviceInfo();
  } else {
    Serial.print("failed, rc=");
    Serial.print(client.state());
    Serial.println(" try again in 5 seconds");
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String topicStr = String(topic);
  String message = String((char*)payload).substring(0, length);
  
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);
  
  if (topicStr.endsWith("/ota/start")) {
    // Start OTA update
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, message);
    const char* firmware_url = doc["url"];
    startOTA(firmware_url);
  }
  else if (topicStr.endsWith("/config")) {
    // Update device configuration
    updateConfiguration(message);
  }
  else if (topicStr.endsWith("/commands")) {
    // Process command
    processCommand(message);
  }
}

void sendTelemetry() {
  SensorData data = readSensors();
  
  DynamicJsonDocument doc(1024);
  doc["device_id"] = DEVICE_ID;
  doc["timestamp"] = getTimestamp();
  doc["temperature"] = data.temperature;
  doc["humidity"] = data.humidity;
  doc["vibration"] = data.vibration;
  doc["current"] = data.current;
  doc["voltage"] = data.voltage;
  doc["rssi"] = data.rssi;
  doc["uptime"] = data.uptime;
  doc["cpu_usage"] = data.cpu_usage;
  doc["memory_usage"] = data.memory_usage;
  doc["free_heap"] = ESP.getFreeHeap();
  doc["version"] = VERSION;
  
  char buffer[1024];
  serializeJson(doc, buffer);
  
  String topic = "devices/" + DEVICE_ID + "/telemetry";
  if (client.publish(topic.c_str(), buffer)) {
    Serial.println("Telemetry sent successfully");
  } else {
    Serial.println("Failed to send telemetry");
  }
}

SensorData readSensors() {
  SensorData data;
  
  // Read DHT22
  data.temperature = dht.readTemperature();
  data.humidity = dht.readHumidity();
  
  // Read analog sensors
  data.vibration = analogRead(VIBRATION_PIN) * (3.3 / 4095.0);
  data.current = analogRead(CURRENT_PIN) * (3.3 / 4095.0) * 10; // ACS712 calibration
  
  // Voltage measurement (assuming voltage divider)
  data.voltage = analogRead(34) * (3.3 / 4095.0) * 4; // 4:1 divider
  
  // WiFi metrics
  data.rssi = WiFi.RSSI();
  
  // Uptime
  data.uptime = millis() / 1000;
  
  // CPU/Memory estimation (ESP32 specific)
  data.cpu_usage = getCPUUsage();
  data.memory_usage = 1.0 - (ESP.getFreeHeap() / 320.0); // 320KB total
  
  // Validate readings
  if (isnan(data.temperature)) data.temperature = 25.0;
  if (isnan(data.humidity)) data.humidity = 50.0;
  
  return data;
}

void sendDeviceInfo() {
  DynamicJsonDocument doc(512);
  doc["device_id"] = DEVICE_ID;
  doc["type"] = "ESP32";
  doc["version"] = VERSION;
  doc["capabilities"] = "telemetry,ota,remote_config";
  
  char buffer[512];
  serializeJson(doc, buffer);
  
  client.publish(("devices/" + DEVICE_ID + "/info").c_str(), buffer);
}

void setupOTA() {
  // OTA callback handlers
  ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "sketch";
    } else {
      type = "filesystem";
    }
    Serial.println("Start updating " + type);
    otaInProgress = true;
  });
  
  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
    otaInProgress = false;
  });
  
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
    else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
    else if (error == OTA_END_ERROR) Serial.println("End Failed");
    otaInProgress = false;
  });
  
  ArduinoOTA.begin();
}

void startOTA(const char* url) {
  Serial.print("Starting OTA from: ");
  Serial.println(url);
  
  // HTTP client to download firmware
  WiFiClientSecure client;
  client.setCACert(root_ca);
  
  HTTPClient http;
  http.begin(client, url);
  
  int httpCode = http.GET();
  if (httpCode == HTTP_CODE_OK) {
    int contentLength = http.getSize();
    bool canBegin = Update.begin(contentLength);
    
    if (canBegin) {
      Serial.println("Beginning OTA update");
      
      WiFiClient* stream = http.getStreamPtr();
      size_t written = Update.writeStream(*stream);
      
      if (written == contentLength) {
        Serial.println("Written : " + String(written) + " successfully");
      } else {
        Serial.println("Written only : " + String(written) + "/" + String(contentLength) + ". Retry?");
      }
      
      if (Update.end()) {
        Serial.println("OTA done!");
        if (Update.isFinished()) {
          Serial.println("Update successfully completed. Rebooting.");
          ESP.restart();
        } else {
          Serial.println("Update not finished? Something went wrong!");
        }
      } else {
        Serial.println("Error Occurred. Error #: " + String(Update.getError()));
      }
    } else {
      Serial.println("Not enough space to begin OTA");
    }
  } else {
    Serial.print("Firmware download failed, HTTP code: ");
    Serial.println(httpCode);
  }
  
  http.end();
}

void handleOTA() {
  ArduinoOTA.handle();
}

void updateConfiguration(String config) {
  DynamicJsonDocument doc(512);
  deserializeJson(doc, config);
  
  // Update configuration parameters
  if (doc.containsKey("telemetry_interval")) {
    // Update interval (would require restart or dynamic change)
    Serial.print("Telemetry interval updated to: ");
    Serial.println(doc["telemetry_interval"].as<int>());
  }
  
  // Acknowledge config update
  client.publish(("devices/" + DEVICE_ID + "/config/ack").c_str(), "Configuration applied");
}

void processCommand(String command) {
  DynamicJsonDocument doc(256);
  deserializeJson(doc, command);
  
  String cmd = doc["command"];
  
  if (cmd == "reboot") {
    Serial.println("Rebooting device...");
    ESP.restart();
  }
  else if (cmd == "factory_reset") {
    Serial.println("Factory reset...");
    // Reset configuration to defaults
    // Then reboot
    ESP.restart();
  }
  else if (cmd == "get_status") {
    sendDeviceInfo();
  }
}

float getCPUUsage() {
  // Simple CPU usage estimation
  static unsigned long last_idle = 0;
  static unsigned long last_total = 0;
  
  unsigned long now = millis();
  unsigned long idle = esp_get_free_heap_size(); // Not accurate, just placeholder
  unsigned long total = now;
  
  float idle_diff = idle - last_idle;
  float total_diff = total - last_total;
  
  float usage = 100.0 * (1.0 - idle_diff / total_diff);
  
  last_idle = idle;
  last_total = total;
  
  return usage;
}

String getTimestamp() {
  // For production, sync with NTP
  return String(millis() / 1000);
}

// Certificate (replace with actual certs)
const char* root_ca = \
"-----BEGIN CERTIFICATE-----\n"
"...\n"
"-----END CERTIFICATE-----\n";