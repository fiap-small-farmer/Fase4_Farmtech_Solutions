#include <DHT.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <WiFiUdp.h>
#include <NTPClient.h>

struct DateTime {
  char date[11]; // 1 - SUBSTITUÍ STRING POR CHAR[] PARA ECONOMIZAR MEMÓRIA.
  char time[9];
};

// Credenciais da rede WiFi
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// Endereço do servidor MQTT
const char* mqtt_server = "broker.mqtt-dashboard.com";
WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE (200)
char msg[MSG_BUFFER_SIZE];

const uint16_t mqtt_port = 1883; // 2 - USANDO UINT16_T PARA ECONOMIZAR MEMÓRIA.

#define DHTPIN 23
#define DHTTYPE DHT22
#define LDR_PIN 34
#define BTN_PHOSPHORUS 22
#define BTN_POTASSIUM 21
#define RELAY_PIN 19
#define LED_RED 18

DHT dht(DHTPIN, DHTTYPE);

uint16_t moistureThreshold = 600; // 3 - REPRESENTANDO UMIDADE COMO INTEIRO (600 = 60.0%).
uint16_t phMin = 60; // 4 - pH REPRESENTADO COMO INTEIRO (6.0 -> 60).
uint16_t phMax = 80; // 4 - pH REPRESENTADO COMO INTEIRO (8.0 -> 80).

uint8_t phosphorusDetected = 0; // 5 - USANDO UINT8_T PARA FLAGS BOOLEANAS.
uint8_t potassiumDetected = 0;
uint8_t irrigation = 0;

WiFiUDP udp;
NTPClient timeClient(udp, "pool.ntp.org", 0, 3600 * 24);

// Função para conectar à rede Wi-Fi
void setup_wifi() {
  Serial.println();
  Serial.print("Conectando a ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print("...");
  }

  Serial.println("\nWiFi conectado");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

// Função para conectar ao servidor MQTT
void reconnect() {
  while (!client.connected()) {
    Serial.print("Tentando conectar ao MQTT...");
    char clientId[25];
    snprintf(clientId, sizeof(clientId), "ESP32Client-%04X", random(0xffff)); // 6 - USANDO SNPRINTF PARA SEGURANÇA.

    if (client.connect(clientId)) {
      Serial.println("MQTT conectado");
      client.subscribe("inTopic");
    } else {
      Serial.print("Falha, código de retorno=");
      Serial.print(client.state());
      Serial.println(". Tentando novamente em 5 segundos...");
      delay(5000);
    }
  }
}

// Função para configurar os pinos de entrada e saída
void setup_pins() {
  pinMode(LDR_PIN, INPUT);
  pinMode(BTN_PHOSPHORUS, INPUT_PULLUP);
  pinMode(BTN_POTASSIUM, INPUT_PULLUP);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_RED, OUTPUT);

  digitalWrite(RELAY_PIN, LOW);
  digitalWrite(LED_RED, LOW);
}

// Função para ler os sensores de umidade (DHT) e pH (simulado pelo LDR)
void read_sensors(uint16_t &humidity, uint16_t &phValue) {
  float rawHumidity = dht.readHumidity();
  humidity = (uint16_t)(rawHumidity * 10); // 3 - CONVERTENDO PARA INTEIRO (60.0 -> 600).
  int ldrValue = analogRead(LDR_PIN);
  phValue = (uint16_t)map(ldrValue, 0, 4095, 0, 140); // 4 - CONVERTENDO pH (0 -> 14.0 -> 140).
}

// Função para verificar a detecção de nutrientes (Fósforo e Potássio)
void check_nutrients() {
  phosphorusDetected = !digitalRead(BTN_PHOSPHORUS);
  potassiumDetected = !digitalRead(BTN_POTASSIUM);
}

// Função para controlar o LED vermelho, indicando se há nutrientes detectados
void control_red_led() {
  digitalWrite(LED_RED, phosphorusDetected || potassiumDetected);
}

// Função para controlar o relé de irrigação com base na umidade, pH e nutrientes
void control_relay(uint16_t humidity, uint16_t phValue) {
  if (humidity < moistureThreshold && phValue >= phMin && phValue <= phMax && (phosphorusDetected || potassiumDetected)) {
    digitalWrite(RELAY_PIN, HIGH);
    irrigation = 1;
  } else {
    digitalWrite(RELAY_PIN, LOW);
    irrigation = 0;
  }
}

// Função para obter a data e hora atual via NTP (Network Time Protocol)
DateTime get_current_time() {
  timeClient.update();
  int32_t offset = -3 * 3600;
  unsigned long localTime = timeClient.getEpochTime() + offset;
  time_t time = (time_t)localTime;
  struct tm *ptm = gmtime(&time);

  DateTime dt;
  snprintf(dt.date, sizeof(dt.date), "%02d/%02d/%04d", ptm->tm_mday, ptm->tm_mon + 1, ptm->tm_year + 1900);
  snprintf(dt.time, sizeof(dt.time), "%02d:%02d:%02d", ptm->tm_hour, ptm->tm_min, ptm->tm_sec);

  return dt;
}

// Função para enviar dados dos sensores para o servidor MQTT
void send_mqtt_data(uint16_t humidity, uint16_t phValue, const char* date, const char* time) {
  StaticJsonDocument<200> doc;
  doc["humidade"] = humidity / 10.0; // 3 - CONVERTENDO DE VOLTA PARA FLOAT.
  doc["ph"] = phValue / 10.0; // 4 - CONVERTENDO DE VOLTA PARA FLOAT.
  doc["fosforo"] = phosphorusDetected ? "1" : "0";
  doc["potassio"] = potassiumDetected ? "1" : "0";
  doc["data"] = date;
  doc["hora"] = time;
  doc["irrigacao"] = irrigation;

  serializeJson(doc, msg);
  client.publish("farmTechSolutions", msg);
}

void setup() {
  Serial.begin(115200);
  setup_wifi(); // Conecta-se à rede Wi-Fi
  client.setServer(mqtt_server, mqtt_port); // Configura o servidor MQTT
  dht.begin(); // Inicializa o sensor DHT
  setup_pins(); // Configura os pinos de entrada/saída
  timeClient.begin(); // Inicializa o cliente NTP
}

void loop() {
  if (!client.connected()) {
    reconnect(); // Conecta-se ao servidor MQTT caso não esteja conectado
  }
  client.loop(); // Mantém a comunicação com o broker MQTT

  unsigned long now = millis();
  if (now - lastMsg > 2000) {
    lastMsg = now;

    uint16_t humidity, phValue;
    read_sensors(humidity, phValue); // Lê os sensores
    check_nutrients(); // Verifica os nutrientes
    control_red_led(); // Controla o LED vermelho
    control_relay(humidity, phValue); // Controla o relé de irrigação

    DateTime currentTime = get_current_time(); // Obtém a data e hora atual

    // Exibe os dados no Serial Monitor
    Serial.println(" ");
    Serial.print("Umidade: ");
    Serial.print(humidity / 10.0);
    Serial.println("%");
    Serial.print("pH (simulado pelo LDR): ");
    Serial.println(phValue / 10.0);
    Serial.print("Fósforo: ");
    Serial.println(phosphorusDetected ? "Ativado" : "Desativado");
    Serial.print("Potássio: ");
    Serial.println(potassiumDetected ? "Ativado" : "Desativado");
    Serial.println(irrigation ? "Irrigação: Ativado" : "Irrigação: Desativado");
    Serial.print("Data: ");
    Serial.println(currentTime.date);
    Serial.print("Hora: ");
    Serial.println(currentTime.time);

    send_mqtt_data(humidity, phValue, currentTime.date, currentTime.time); // Envia os dados via MQTT
  }
}