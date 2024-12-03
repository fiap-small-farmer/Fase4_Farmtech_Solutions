import paho.mqtt.client as mqtt  # Biblioteca para comunicação com o broker MQTT
import json  # Biblioteca para manipulação de dados em formato JSON
import time  # Biblioteca para controlar o tempo de espera

# Configurações do broker MQTT
BROKER_ADDRESS = "broker.mqtt-dashboard.com"  
TOPIC = "farmTechSolutions"  

# Variável global para indicar se a mensagem foi recebida
message_received = False

# Callback executado quando o cliente se conecta ao broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao broker MQTT!")  # Conexão bem-sucedida
        client.subscribe(TOPIC)  # Inscrição no tópico
    else:
        print(f"Falha na conexão, código de retorno {rc}")  # Erro na conexão

# Callback executado ao receber uma mensagem no tópico inscrito
def on_message(client, userdata, msg):
    global message_received
    message_received = True  # Marca que uma mensagem foi recebida
    try:
        # Decodifica e processa a mensagem recebida
        payload = json.loads(msg.payload.decode('utf-8'))  

        # Exibe os dados recebidos em formato JSON
        print(payload)

    except json.JSONDecodeError:
        print("Erro ao decodificar a mensagem JSON")  # Tratamento de erro ao interpretar JSON

# Callback executado quando a conexão é perdida
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Conexão com o broker perdida! Tentando reconectar...")  # Exibe mensagem se a conexão cair
    else:
        print("Desconectado do broker MQTT.")  # Exibe mensagem quando desconectado normalmente

# Função para verificar se a mensagem foi recebida dentro de 5 segundos
def check_for_message(timeout=5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if message_received:
            return True
        time.sleep(0.1)  # Espera um pouco antes de checar novamente
    return False

# Configuração do cliente MQTT
client = mqtt.Client()  
client.on_connect = on_connect  # Define o callback de conexão
client.on_message = on_message  # Define o callback de mensagem
client.on_disconnect = on_disconnect  # Define o callback de desconexão

# Conexão com o broker e início do loop principal
try:
    print("Conectando ao broker MQTT...")
    client.connect(BROKER_ADDRESS, 1883, 60)  # Conecta ao broker no endereço e porta padrão
    print(f"Aguardando mensagens no tópico '{TOPIC}'...")

    # Verifica se uma mensagem foi recebida dentro de 5 segundos
    if not check_for_message():
        print("Erro: Nenhuma mensagem recebida, verifique a conexão WiFi!")

    client.loop_forever()  # Mantém o cliente em execução, processando mensagens
except KeyboardInterrupt:
    print("Desconectando...")  # Finaliza a conexão ao interromper o script
    client.disconnect()
except Exception as e:
    print(f"Erro ao conectar ou manter a conexão: {e}")  # Exibe mensagem de erro caso algo aconteça na conexão
