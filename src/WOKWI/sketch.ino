// Bibliotecas
#include <DHT.h> // Biblioteca para o sensor DHT22

// Definição de pinos
#define DHTPIN 23          // Pino do DHT22
#define DHTTYPE DHT22      // Tipo do sensor DHT
#define LDR_PIN 34         // Pino para o sensor LDR (simulando pH)
#define BTN_PHOSPHORUS 22  // Pino do botão para "sensor de Fósforo"
#define BTN_POTASSIUM 21   // Pino do botão para "sensor de Potássio"
#define RELAY_PIN 19       // Pino do relé (bomba d'água)
#define LED_RED 18         // Pino do LED vermelho

// Inicialização do sensor de umidade e temperatura
DHT dht(DHTPIN, DHTTYPE);

// Parâmetros de decisão
float moistureThreshold = 60.0; // Limite de umidade do solo
float phMin = 6.0;              // Limite mínimo de pH para irrigação
float phMax = 8.0;              // Limite máximo de pH para irrigação

// Variáveis de controle
bool phosphorusDetected = false;
bool potassiumDetected = false;

void setup() {
  // Configuração inicial dos pinos
  Serial.begin(115200);
  dht.begin();

  pinMode(LDR_PIN, INPUT);
  pinMode(BTN_PHOSPHORUS, INPUT_PULLUP);
  pinMode(BTN_POTASSIUM, INPUT_PULLUP);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_RED, OUTPUT);

  digitalWrite(RELAY_PIN, LOW); // Relé (bomba) inicialmente desligado
  digitalWrite(LED_RED, LOW);   // LED vermelho inicialmente apagado
}

void loop() {
  // Leitura dos sensores
  float humidity = dht.readHumidity();      // Leitura da umidade do solo
  int ldrValue = analogRead(LDR_PIN);       // Leitura do valor do LDR (simulando pH)
  
  // Mapear o valor do LDR para a faixa de pH de 0 a 14
  float phValue = map(ldrValue, 0, 4095, 0, 14);

  // Verificar o estado dos nutrientes
  phosphorusDetected = !digitalRead(BTN_PHOSPHORUS);
  potassiumDetected = !digitalRead(BTN_POTASSIUM);

  // Exibir leituras no console para monitoramento
  Serial.print("Umidade: ");
  Serial.print(humidity);
  Serial.print("%, pH (simulado pelo LDR): ");
  Serial.print(phValue);
  Serial.print(", Fósforo: ");
  Serial.print(phosphorusDetected ? "Ativado" : "Desativado");
  Serial.print(", Potássio: ");
  Serial.println(potassiumDetected ? "Ativado" : "Desativado");

  // Lógica de controle do LED vermelho
  if (phosphorusDetected || potassiumDetected) {
    digitalWrite(LED_RED, HIGH); // Liga o LED vermelho se qualquer botão estiver pressionado
  } else {
    digitalWrite(LED_RED, LOW);  // Apaga o LED vermelho se ambos os botões estiverem soltos
  }

  // Lógica de controle da bomba d'água
  if (humidity < moistureThreshold && phValue >= phMin && phValue <= phMax && (phosphorusDetected || potassiumDetected)) {
    digitalWrite(RELAY_PIN, HIGH); // Liga a bomba d'água
    Serial.println("Irrigação ativada!");

    // Simular o envio dos dados para o servidor
    Serial.print("Enviando dados para o servidor: ");
    Serial.print("{\"umidade\": "); //umidade
    Serial.print(humidity);
    Serial.print(", \"ph\": "); //ph
    Serial.print(phValue);
    Serial.print(", \"fosforo\": "); //fosforo
    Serial.print(phosphorusDetected ? "1" : "0");
    Serial.print(", \"potassio\": "); //potassio
    Serial.print(potassiumDetected ? "1" : "0");
    Serial.println(", \"timestamp\": \"2024-11-12T14:30:00Z\"}"); // Timestamp

  } else {
    digitalWrite(RELAY_PIN, LOW); // Desliga a bomba d'água
    Serial.println("Irrigação desativada!");
  }

  delay(2000); // Intervalo entre as leituras
}
