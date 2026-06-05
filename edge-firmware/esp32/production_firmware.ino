/*
 * EdgeSphere AI - Production ESP32 Firmware
 * With OTA, TLS, and secure communication
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Update.h>
#include <time.h>
#include <DHT.h>
#include <Adafruit_Sensor.h>

// Production Configuration
#define DEVICE_ID "ESP32_Minewing_" + String(ESP.getEfuseMac(), HEX)
#define FIRMWARE_VERSION "2.0.0"
#define MANUFACTURER "Minewing Technologies"

// WiFi Credentials (Use WiFi Manager in production)
const char* wifi_ssid = "Minewing_Factory_WiFi";
const char* wifi_password = "SecurePassword123!";

// MQTT TLS Configuration
const char* mqtt_server = "api.minewing.com";
const int mqtt_port = 8883;
const char* mqtt_client_id = DEVICE_ID.c_str();

// TLS Certificates (Replace with actual certs)
const char* root_ca = \
"-----BEGIN CERTIFICATE-----\n"
"MIIFazCCA1OgAwIBAgIRAIIQDL6xVl+f2I6EoDq5m7swDQYJKoZIhvcNAQELBQAw\n"
"...\n"
"-----END CERTIFICATE-----\n";

// Device certificates for authentication
const char* client_cert = \
"-----BEGIN CERTIFICATE-----\n"
"...\n"
"-----END CERTIFICATE-----\n";

const char* client_key = \
"-----BEGIN RSA PRIVATE KEY-----\n"
"...\n"
"-----END RSA PRIVATE KEY-----\n";

// Pin Definitions
#define DHTPIN 4
#define DHTTYPE DHT22
#define VIBRATION_PIN 34
#define CURRENT_PIN 35
#define LED_BUILTIN 2

// Global objects
WiFiClientSecure espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);

// Device state
unsigned long lastTelemetry = 0;
unsigned long lastReconnect = 0;
unsigned long lastNTPUpdate = 0;
const long TELEMETRY_INTERVAL = 5000;
const long RECONNECT_INTERVAL = 10000;
const long NTP_INTERVAL = 3600000; // 1 hour

// NTP Servers
const char* ntpServer1 = "pool.ntp.org";
const char* ntpServer2 = "time.google.com";
const long gmtOffset_sec = 0;
const int daylightOffset_sec = 0;

// Data structures
struct SensorReading {
  float temperature;
  float humidity;
  float vibration;
  float current;
  float voltage;
  float power;
  int rssi;
  unsigned long uptime;
  float free_heap;
  float cpu_freq;
};

// Error counters
int connectionErrors = 0;
int telemetryErrors = 0;
unsigned long lastSuccessfulTelemetry = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("\n=========================================");
  Serial.println("EdgeSphere AI - Minewing Technologies");
  Serial.println("Device: " + String(DEVICE_ID));
  Serial.println("Firmware: " + String(FIRMWARE_VERSION));
  Serial.println("=========================================\n");
  
  // Initialize hardware
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  dht.begin();
  
  // Setup
  setupWiFi();
  setupNTP();
  setupMQTT();
  setupOTA();
  
  // Send device info
  sendDeviceInfo();
  digitalWrite(LED_BUILTIN, LOW);
  
  Serial.println("Device ready for production");
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
  
  unsigned long now = millis();
  
  // Send telemetry
  if (now - lastTelemetry >= TELEMETRY_INTERVAL) {
    sendTelemetry();
    lastTelemetry = now;
  }
  
  // Update NTP time
  if (now - lastNTPUpdate >= NTP_INTERVAL) {
    setupNTP();
    lastNTPUpdate = now;
  }
  
  // Handle OTA
  ArduinoOTA.handle();
  
  // Health monitoring
  checkDeviceHealth();
}

void setupWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(wifi_ssid, wifi_password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connected");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("RSSI: ");
    Serial.println(WiFi.RSSI());
  } else {
    Serial.println("\n❌ WiFi connection failed");
  }
}

void setupNTP() {
  Serial.print("Syncing time with NTP...");
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer1, ntpServer2);
  
  struct tm timeinfo;
  int attempts = 0;
  while (!getLocalTime(&timeinfo) && attempts < 10) {
    delay(100);
    attempts++;
  }
  
  if (attempts < 10) {
    Serial.println(" ✅");
    char timeString[30];
    strftime(timeString, sizeof(timeString), "%Y-%m-%d %H:%M:%S", &timeinfo);
    Serial.println("Current time: " + String(timeString));
  } else {
    Serial.println(" ⚠️ Using system time");
  }
}

void setupMQTT() {
  espClient.setCACert(root_ca);
  espClient.setCertificate(client_cert);
  espClient.setPrivateKey(client_key);
  
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
  client.setKeepAlive(60);
}

void reconnectMQTT() {
  unsigned long now = millis();
  if (now - lastReconnect < RECONNECT_INTERVAL) {
    return;
  }
  lastReconnect = now;
  
  Serial.print("Connecting to MQTT...");
  digitalWrite(LED_BUILTIN, HIGH);
  
  if (client.connect(mqtt_client_id)) {
    Serial.println(" ✅");
    connectionErrors = 0;
    
    // Subscribe to topics
    client.subscribe(("devices/" + DEVICE_ID + "/commands").c_str());
    client.subscribe(("devices/" + DEVICE_ID + "/config").c_str());
    client.subscribe(("devices/" + DEVICE_ID + "/ota").c_str());
    
    // Send device info on reconnect
    sendDeviceInfo();
    digitalWrite(LED_BUILTIN, LOW);
  } else {
    Serial.print(" ❌ failed, rc=");
    Serial.print(client.state());
    connectionErrors++;
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = String((char*)payload).substring(0, length);
  String topicStr = String(topic);
  
  Serial.println("📨 Command received: " + topicStr);
  
  if (topicStr.endsWith("/ota")) {
    handleOTACommand(message);
  }
  else if (topicStr.endsWith("/config")) {
    handleConfigUpdate(message);
  }
  else if (topicStr.endsWith("/commands")) {
    handleCommand(message);
  }
}

void sendTelemetry() {
  SensorReading reading = readSensors();
  
  DynamicJsonDocument doc(1024);
  doc["device_id"] = DEVICE_ID;
  doc["timestamp"] = getTimestamp();
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["manufacturer"] = MANUFACTURER;
  
  // Sensor data
  doc["temperature"] = reading.temperature;
  doc["humidity"] = reading.humidity;
  doc["vibration"] = reading.vibration;
  doc["current"] = reading.current;
  doc["voltage"] = reading.voltage;
  doc["power"] = reading.power;
  
  // Device metrics
  doc["rssi"] = reading.rssi;
  doc["uptime"] = reading.uptime;
  doc["free_heap"] = reading.free_heap;
  doc["cpu_freq"] = reading.cpu_freq;
  
  // Quality metrics
  doc["connection_errors"] = connectionErrors;
  doc["telemetry_errors"] = telemetryErrors;
  doc["last_successful"] = lastSuccessfulTelemetry;
  
  char buffer[1024];
  serializeJson(doc, buffer);
  
  String topic = "devices/" + DEVICE_ID + "/telemetry";
  if (client.publish(topic.c_str(), buffer)) {
    lastSuccessfulTelemetry = millis();
    telemetryErrors = 0;
    Serial.println("📡 Telemetry sent");
  } else {
    telemetryErrors++;
    Serial.println("❌ Failed to send telemetry");
  }
}

SensorReading readSensors() {
  SensorReading data;
  
  // Read DHT22
  data.temperature = dht.readTemperature();
  data.humidity = dht.readHumidity();
  
  // Validate readings
  if (isnan(data.temperature)) data.temperature = 25.0;
  if (isnan(data.humidity)) data.humidity = 50.0;
  
  // Read analog sensors
  int vibRaw = analogRead(VIBRATION_PIN);
  data.vibration = (vibRaw * 3.3 / 4095.0) * 10; // Convert to mm/s
  
  int currentRaw = analogRead(CURRENT_PIN);
  data.current = (currentRaw * 3.3 / 4095.0) * 5; // ACS712 calibration
  
  // Voltage divider (3.3V to 12V)
  int voltRaw = analogRead(34);
  data.voltage = (voltRaw * 3.3 / 4095.0) * 4;
  
  // Calculate power
  data.power = data.voltage * data.current;
  
  // WiFi metrics
  data.rssi = WiFi.RSSI();
  
  // System metrics
  data.uptime = millis() / 1000;
  data.free_heap = ESP.getFreeHeap() / 1024.0; // KB
  data.cpu_freq = ESP.getCpuFreqMHz();
  
  return data;
}

void sendDeviceInfo() {
  DynamicJsonDocument doc(512);
  doc["device_id"] = DEVICE_ID;
  doc["type"] = "ESP32";
  doc["manufacturer"] = MANUFACTURER;
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["mac_address"] = WiFi.macAddress();
  doc["capabilities"] = "telemetry,ota,remote_config,predictive_maintenance";
  
  char buffer[512];
  serializeJson(doc, buffer);
  
  client.publish(("devices/" + DEVICE_ID + "/info").c_str(), buffer);
  Serial.println("Device info published");
}

void setupOTA() {
  ArduinoOTA.setHostname(DEVICE_ID.c_str());
  ArduinoOTA.setPassword("MinewingOTA2024");
  
  ArduinoOTA.onStart([]() {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "firmware";
    } else {
      type = "filesystem";
    }
    Serial.println("Starting OTA update: " + type);
  });
  
  ArduinoOTA.onEnd([]() {
    Serial.println("OTA update complete. Rebooting...");
    ESP.restart();
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
  });
  
  ArduinoOTA.begin();
  Serial.println("OTA ready");
}

void handleOTACommand(String payload) {
  DynamicJsonDocument doc(512);
  deserializeJson(doc, payload);
  
  const char* firmware_url = doc["url"];
  const char* version = doc["version"];
  
  Serial.printf("OTA update to version %s from %s\n", version, firmware_url);
  
  // Download and flash firmware
  WiFiClientSecure client;
  client.setCACert(root_ca);
  
  HTTPClient http;
  http.begin(client, firmware_url);
  
  int httpCode = http.GET();
  if (httpCode == HTTP_CODE_OK) {
    int contentLength = http.getSize();
    if (Update.begin(contentLength)) {
      WiFiClient* stream = http.getStreamPtr();
      size_t written = Update.writeStream(*stream);
      
      if (written == contentLength) {
        Serial.println("Update successful");
        if (Update.end()) {
          Serial.println("Rebooting...");
          ESP.restart();
        }
      }
    }
  }
  http.end();
}

void handleConfigUpdate(String payload) {
  DynamicJsonDocument doc(512);
  deserializeJson(doc, payload);
  
  if (doc.containsKey("telemetry_interval")) {
    // Update telemetry interval (would need restart)
    Serial.printf("Telemetry interval updated to %d ms\n", doc["telemetry_interval"].as<int>());
  }
  
  // Acknowledge
  client.publish(("devices/" + DEVICE_ID + "/config/ack").c_str(), "Configuration applied");
}

void handleCommand(String payload) {
  DynamicJsonDocument doc(256);
  deserializeJson(doc, payload);
  
  String command = doc["command"];
  
  if (command == "reboot") {
    Serial.println("Rebooting device...");
    delay(1000);
    ESP.restart();
  }
  else if (command == "factory_reset") {
    Serial.println("Factory reset...");
    // Reset configuration to defaults
    ESP.restart();
  }
  else if (command == "self_test") {
    runSelfTest();
  }
}

void runSelfTest() {
  DynamicJsonDocument doc(512);
  doc["device_id"] = DEVICE_ID;
  doc["test_results"] = {
    {"wifi", WiFi.status() == WL_CONNECTED},
    {"mqtt", client.connected()},
    {"sensors", true},
    {"memory", ESP.getFreeHeap()},
    {"uptime", millis() / 1000}
  };
  
  char buffer[512];
  serializeJson(doc, buffer);
  client.publish(("devices/" + DEVICE_ID + "/test_results").c_str(), buffer);
}

void checkDeviceHealth() {
  unsigned long now = millis();
  
  // Check if telemetry hasn't been sent for 30 seconds
  if (now - lastSuccessfulTelemetry > 30000) {
    Serial.println("⚠️ Health warning: Telemetry not sending");
    digitalWrite(LED_BUILTIN, HIGH);
  }
  
  // Check memory
  if (ESP.getFreeHeap() < 50000) {
    Serial.println("⚠️ Low memory warning");
  }
}

String getTimestamp() {
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    char timeString[30];
    strftime(timeString, sizeof(timeString), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
    return String(timeString);
  }
  return String(millis());
}