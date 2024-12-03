#include <DHT.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <WiFiUdp.h>
#include <NTPClient.h>

// Estrutura para armazenar a data e a hora
struct DateTime {
  String date; // Armazena a data no formato "dd/mm/yyyy"
  String time; // Armazena o horário no formato "hh:mm:ss"
};

// Credenciais da rede WiFi
const char* ssid = "Wokwi-GUEST"; // Nome da rede WiFi
const char* password = ""; // Senha da rede WiFi (neste caso, vazia)

// Endereço do servidor MQTT
const char* mqtt_server = "broker.mqtt-dashboard.com"; // Servidor MQTT usado para publicar e assinar tópicos
WiFiClient espClient; // Cliente WiFi
PubSubClient client(espClient); // Cliente MQTT utilizando a conexão WiFi

unsigned long lastMsg = 0; // Timestamp da última mensagem enviada via MQTT
#define MSG_BUFFER_SIZE (200) // Tamanho máximo do buffer da mensagem MQTT
char msg[MSG_BUFFER_SIZE]; // Buffer para armazenar mensagens MQTT

const int mqtt_port = 1883; // Porta do servidor MQTT

// Configuração dos pinos usados no hardware
#define DHTPIN 23 // Pino onde o sensor DHT está conectado
#define DHTTYPE DHT22 // Tipo de sensor DHT utilizado
#define LDR_PIN 34 // Pino analógico conectado ao LDR
#define BTN_PHOSPHORUS 22 // Botão para simular a detecção de fósforo
#define BTN_POTASSIUM 21 // Botão para simular a detecção de potássio
#define RELAY_PIN 19 // Pino de controle do relé
#define LED_RED 18 // Pino do LED vermelho

DHT dht(DHTPIN, DHTTYPE); // Objeto para interagir com o sensor DHT

// Limiares de controle para sensores
float moistureThreshold = 60.0; // Umidade mínima para ativar a irrigação
float phMin = 6.0; // Valor mínimo de pH aceitável
float phMax = 8.0; // Valor máximo de pH aceitável

// Estados de nutrientes e irrigação
bool phosphorusDetected = false; // Indica se fósforo foi detectado
bool potassiumDetected = false; // Indica se potássio foi detectado
bool irrigation = false; // Indica se a irrigação está ativa

WiFiUDP udp; // Cliente UDP para comunicação NTP
NTPClient timeClient(udp, "pool.ntp.org", 0, 3600 * 24); // Cliente NTP para sincronizar a hora

// Função para conectar ao WiFi
void setup_wifi() {
  Serial.println();
  Serial.print("Conectando a ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA); // Configura o modo como estação (cliente)
  WiFi.begin(ssid, password); // Inicia a conexão com a rede WiFi

  while (WiFi.status() != WL_CONNECTED) {
    delay(500); // Aguarda a conexão
    Serial.print("...");
  }

  Serial.println("\nWiFi conectado");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP()); // Imprime o endereço IP obtido
}

// Função para reconectar ao servidor MQTT, caso a conexão seja perdida
void reconnect() {
  while (!client.connected()) {
    Serial.print("Tentando conectar ao MQTT...");
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX); // Gera um ID de cliente aleatório

    if (client.connect(clientId.c_str())) {
      Serial.println("MQTT conectado");
      client.subscribe("inTopic"); // Inscreve-se no tópico "inTopic"
    } else {
      Serial.print("Falha, código de retorno=");
      Serial.print(client.state());
      Serial.println(". Tentando novamente em 5 segundos...");
      delay(5000); // Aguarda antes de tentar reconectar
    }
  }
}

// Configura os pinos como entrada ou saída
void setup_pins() {
  pinMode(LDR_PIN, INPUT); // Configura o pino do LDR como entrada
  pinMode(BTN_PHOSPHORUS, INPUT_PULLUP); // Botão de fósforo com resistor pull-up
  pinMode(BTN_POTASSIUM, INPUT_PULLUP); // Botão de potássio com resistor pull-up
  pinMode(RELAY_PIN, OUTPUT); // Pino do relé como saída
  pinMode(LED_RED, OUTPUT); // Pino do LED vermelho como saída

  digitalWrite(RELAY_PIN, LOW); // Relé desligado inicialmente
  digitalWrite(LED_RED, LOW); // LED vermelho desligado inicialmente
}

// Lê os sensores e simula o valor de pH com o LDR
void read_sensors(float &humidity, float &phValue) {
  humidity = dht.readHumidity(); // Lê a umidade do sensor DHT
  int ldrValue = analogRead(LDR_PIN); // Lê o valor do LDR
  phValue = map(ldrValue, 0, 4095, 0, 14); // Converte o valor do LDR para escala de pH
}

// Verifica o estado dos botões para detectar nutrientes
void check_nutrients() {
  phosphorusDetected = !digitalRead(BTN_PHOSPHORUS); // Detecta fósforo
  potassiumDetected = !digitalRead(BTN_POTASSIUM); // Detecta potássio
}

// Controla o LED vermelho com base nos nutrientes detectados
void control_red_led() {
  digitalWrite(LED_RED, phosphorusDetected || potassiumDetected);
}

// Controla o relé para ativar/desativar a irrigação
void control_relay(float humidity, float phValue) {
  if (humidity < moistureThreshold && phValue >= phMin && phValue <= phMax && (phosphorusDetected || potassiumDetected)) {
    digitalWrite(RELAY_PIN, HIGH); // Ativa o relé
    irrigation = true; // Irrigação ativa
  } else {
    digitalWrite(RELAY_PIN, LOW); // Desativa o relé
    irrigation = false; // Irrigação desativada
  }
}

// Obtém a data e a hora atual usando NTP
DateTime get_current_time() {
  timeClient.update(); // Atualiza a hora do cliente NTP
  int offset = -3 * 3600; // Ajuste para o fuso horário GMT-3
  unsigned long localTime = timeClient.getEpochTime() + offset;
  time_t time = (time_t)localTime;
  struct tm *ptm = gmtime(&time);

  char formattedDate[11]; // Buffer para a data formatada
  sprintf(formattedDate, "%02d/%02d/%04d", ptm->tm_mday, ptm->tm_mon + 1, ptm->tm_year + 1900);

  char formattedTime[9]; // Buffer para a hora formatada
  sprintf(formattedTime, "%02d:%02d:%02d", ptm->tm_hour, ptm->tm_min, ptm->tm_sec);

  return {String(formattedDate), String(formattedTime)}; // Retorna a data e hora como String
}

// Envia os dados coletados para o servidor MQTT no formato JSON
void send_mqtt_data(float humidity, float phValue, String date, String time) {
  StaticJsonDocument<200> doc; // Cria um documento JSON para serialização
  doc["humidade"] = humidity;
  doc["ph"] = phValue;
  doc["fosforo"] = phosphorusDetected ? "1" : "0";
  doc["potassio"] = potassiumDetected ? "1" : "0";
  doc["data"] = date;
  doc["hora"] = time;
  doc["irrigacao"] = irrigation;

  serializeJson(doc, msg); // Serializa o JSON para o buffer de mensagem
  client.publish("farmTechSolutions", msg); // Publica no tópico MQTT
}

// Configuração inicial do sistema
void setup() {
  Serial.begin(115200); // Inicializa a comunicação serial
  setup_wifi(); // Conecta ao WiFi
  client.setServer(mqtt_server, mqtt_port); // Configura o servidor MQTT
  dht.begin(); // Inicializa o sensor DHT
  setup_pins(); // Configura os pinos
  timeClient.begin(); // Inicializa o cliente NTP
}

// Loop principal para leitura de sensores, controle e envio de dados
void loop() {
  if (!client.connected()) {
    reconnect(); // Reconecta ao servidor MQTT, se necessário
  }
  client.loop(); // Mantém a conexão MQTT ativa

  unsigned long now = millis();
  if (now - lastMsg > 2000) { // Executa a cada 2 segundos
    lastMsg = now;

    float humidity, phValue;
    read_sensors(humidity, phValue); // Lê os sensores
    check_nutrients(); // Verifica nutrientes
    control_red_led(); // Atualiza o estado do LED vermelho
    control_relay(humidity, phValue); // Controla o relé

    DateTime currentTime = get_current_time(); // Obtém data e hora atual

    // Exibe leituras no console para monitoramento
    Serial.println(" ");
    Serial.print("Umidade: ");
    Serial.print(humidity);
    Serial.println("%");
    Serial.print("pH (simulado pelo LDR): ");
    Serial.println(phValue);
    Serial.print("Fósforo: ");
    Serial.println(phosphorusDetected ? "Ativado" : "Desativado");
    Serial.print("Potássio: ");
    Serial.println(potassiumDetected ? "Ativado" : "Desativado");
    Serial.println(irrigation ? "Irrigação: Ativado" : "Irrigação: desativado");
    Serial.print("Data: ");
    Serial.println(currentTime.date);
    Serial.print("Hora: ");
    Serial.println(currentTime.time);

    // Envia os dados de umidade, pH, data e hora para o servidor MQTT
    send_mqtt_data(humidity, phValue, currentTime.date, currentTime.time);
  }
}